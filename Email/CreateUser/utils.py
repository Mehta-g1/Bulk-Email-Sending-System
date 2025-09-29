from django.core.mail import EmailMessage, get_connection, send_mail, EmailMultiAlternatives
from .models import emailUsers, Receipent, reset_link
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import get_object_or_404
from EmailTemplates.models import Template
from django.contrib import messages
import pandas as pd
from io import BytesIO



def profileCompletetion(user):
    total_fields,filled_fields,=12,0
    fields_to_check = [
        user.name,
        user.email_address,
        user.post,
        user.department,
        user.about_you,
        user.personalEmail,
        user.org_name,
        user.dob,
        user.address,
        user.phone,
        user.email_password,
        user.image if user.image and user.image.name != 'default.png' else None
    ]

    # Count filled fields
    for field in fields_to_check:
        if field not in [None, '', 'default.png']:
            filled_fields += 1

    # Calculate completion percentage
    completion_percentage = (filled_fields / total_fields) * 100
    # print(completion_percentage)
    return int(completion_percentage)


# Utilities functions

def get_filtered_recipients(user_id, selected_ids):
    recipients = Receipent.objects.filter(Sender__id=user_id, id__in=selected_ids)
    return [r.email for r in recipients]

def update_recipients_send_time(selected_ids):
    receipients = Receipent.objects.filter(id__in=selected_ids)
    for r in receipients:
        r.send_time+=1
        r.save()
    


def send_bulk_email(user_id,selected_ids):
    account = emailUsers.objects.get(id=user_id)
    try:
        connection = get_connection(
            host=account.email_host,
            port=account.email_port,
            username=account.email_address,
            password=account.email_password,
            use_tls=account.use_tls,
        )
        template = Template.objects.get(user=get_object_or_404(emailUsers, id=user_id),primary=True)

        email = EmailMessage(
            subject=template.subject,
            body=template.body,
            from_email=account.email_address,
            to=get_filtered_recipients(user_id, selected_ids),
            connection=connection,
        )
        email.send()
        template.no_of_time_used =int(template.no_of_time_used) + len(selected_ids)
        template.save()


        update_recipients_send_time(selected_ids)
    except Exception as e:
        print('\n\n--------------------')
        print("Error:",e)
        print("---------------------\n\n")
        return False
    return True


def send_forget_password_link(user_email, token):
    """
    Sends a password reset link to the given user email.
    """
    reset_link = f"http://127.0.0.1:8000/user/reset-password/{token}/"

    subject = "Reset Your Password"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]

    # Plain text fallback (in case user's email doesn't support HTML)
    text_content = f"Please reset your password using the following link: {reset_link}"

    # HTML content
    html_content = f"""
    <html>
    <body>
        <p>We received a request to reset your password.</p>
        <p>
            <a href="{reset_link}" style="
                display: inline-block;
                padding: 10px 20px;
                font-size: 16px;
                color: #fff;
                background-color: #007bff;
                text-decoration: none;
                border-radius: 5px;
                margin: 10px 0;
            ">Reset Password</a>
        </p>
        <p>If you did not request this, you can safely ignore this email.</p>
        <p>Thanks,<br>Email Sender Team</p>
    </body>
    </html>
    """

    # Create email
    msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def check_token(token):
    Token = get_object_or_404(reset_link, token = token)
    if not Token:
        print("Invalid Token")
        return False
    if Token.is_attempted:
        print("Already used token")
        return False
    timediff = now() - Token.datetime  
    print("\nSending time: ", Token.datetime)
    print("Current time:", now())
    print("Difference:", timediff)
    if timediff > timedelta(minutes=15):
        return False
    return True






def extract_receipients_from_file(user, file, request):
    if not file.file:
        messages.warning(request, "No file found or Crupted file. Please upload again CSV/XLS/XLSX file.")
        return False
    try:
        if file.file_type.lower() == 'csv':
            # CSV read
            df = pd.read_csv(file.file)
        else:
            # Excel read (wrap in BytesIO)
            file.file.open('rb')
            df = pd.read_excel(BytesIO(file.file.read()), engine='openpyxl')
            file.file.close()
    except Exception as e:
        print("Error reading file:", e)
        messages.warning(request, "There was an error reading the file. Please ensure it is a valid CSV/XLS/XLSX file.")
        return False
    try:
        # Rename columns
        df.columns = ["name", "email", "category", "comments"]

        added_count = 0
        for _, row in df.iterrows():
            name = row['name']
            email = row['email']
            category = row['category']
            comments = row['comments']

            if not Receipent.objects.filter(Sender=user, email=email).exists():
                Receipent.objects.create(
                    Sender=user,
                    name=name,
                    email=email,
                    receipent_category=category,   # 🔹 Fix: field name `receipent_category`
                    comment=comments,              # 🔹 Fix: field name `comment`
                    source=f"File Upload - {file.file_name}"
                )
                added_count += 1
            else:
                messages.warning(request, f"Email {email} already exists and was skipped.")
        messages.success(request, f"{added_count} recipients added successfully.")
    except Exception as e:
        print("Error processing file:", e)
        messages.error(request, "There was an error processing the file. Please ensure it has the correct format.")
        return False

    return True


