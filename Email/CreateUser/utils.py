from django.core.mail import EmailMessage, get_connection, send_mail, EmailMultiAlternatives
from .models import emailUsers, Receipent, reset_link
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import get_object_or_404
from EmailTemplates.models import Template
from django.contrib import messages
from django.db import transaction
from django.contrib.sites.shortcuts import get_current_site
import pandas as pd
from io import BytesIO
import re
import logging

# Configure Logger
logger = logging.getLogger(__name__)

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
    


def send_bulk_email(user_id, selected_ids):
    account = emailUsers.objects.get(id=user_id)

    # Normalize and prepare defaults
    host = account.email_host.lower().strip()
    port = account.email_port or 587
    use_tls = account.use_tls
    use_ssl = False

    # --- Auto configuration per provider ---
    if 'zoho' in host:
        host = 'smtp.zoho.in' if host.endswith('.in') else 'smtp.zoho.com'
        port = 465
        use_ssl = True
        use_tls = False

    elif 'gmail' in host:
        host = 'smtp.gmail.com'
        port = 587
        use_tls = True
        use_ssl = False

    elif 'outlook' in host or 'office365' in host or 'live' in host:
        host = 'smtp.office365.com'
        port = 587
        use_tls = True
        use_ssl = False

    elif 'yahoo' in host:
        host = 'smtp.mail.yahoo.com'
        port = 465
        use_ssl = True
        use_tls = False

    elif 'icloud' in host or 'me.com' in host:
        host = 'smtp.mail.me.com'
        port = 587
        use_tls = True
        use_ssl = False

    try:
        # Explicitly clear both TLS/SSL defaults
        connection = get_connection(
            host=host,
            port=port,
            username=account.email_address,
            password=account.email_password,
            use_tls=False,
            use_ssl=False,
        )

        # Now enable only one
        if use_ssl:
            connection.use_ssl = True
        elif use_tls:
            connection.use_tls = True

        # Test connection with your template
        template = Template.objects.get(
            user=get_object_or_404(emailUsers, id=user_id),
            primary=True
        )

        email = EmailMessage(
            subject=template.subject,
            body=template.body,
            from_email=account.email_address,
            to=get_filtered_recipients(user_id, selected_ids),
            connection=connection,
        )
        email.content_subtype = "html"
        email.send()

        # Update info
        template.no_of_time_used = int(template.no_of_time_used) + len(selected_ids)
        template.save()
        update_recipients_send_time(selected_ids)

    except Exception as e:
        logger.error(f"Error while sending email: {e}")
        return False

    return True

def send_forget_password_link(request, user_email, token):
    """
    Sends a password reset link to the given user email.
    Uses dynamic domain from request.
    """
    current_site = get_current_site(request)
    domain = current_site.domain
    protocol = 'https' if request.is_secure() else 'http'
    
    reset_link = f"{protocol}://{domain}/user/reset-password/{token}/"

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
        logger.warning("Invalid Token accessed")
        return False
    if Token.is_attempted:
        logger.warning("Attempted to use already used token")
        return False
    timediff = now() - Token.datetime  
    logger.info(f"Token check: Sending time: {Token.datetime}, Current time: {now()}, Diff: {timediff}")
    
    if timediff > timedelta(minutes=15):
        return False
    return True

def is_validEmail(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.fullmatch(pattern, email):
        return True
    return False


def extract_receipients_from_file(user, file, group,  request):
    if not file.file:
        messages.warning(request, "No file found or corrupted file. Please upload again CSV/XLS/XLSX file.")
        return False
    
    try:
        if file.file_type.lower() == 'csv':
            df = pd.read_csv(file.file)
        else:
            # Excel read (wrap in BytesIO)
            file.file.open('rb')
            df = pd.read_excel(BytesIO(file.file.read()), engine='openpyxl')
            file.file.close()
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        messages.warning(request, "There was an error reading the file. Please ensure it is a valid CSV/XLS/XLSX file.")
        return False
        
    try:
        # Normalize columns to lowercase to find matches
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        # Smart Column Matching
        name_col = next((c for c in df.columns if c in ['name', 'fullname', 'user', 'username', 'client']), None)
        email_col = next((c for c in df.columns if c in ['email', 'email_address', 'e-mail', 'mail']), None)
        category_col = next((c for c in df.columns if c in ['category', 'type', 'designation']), 'category') # default if exists
        comment_col = next((c for c in df.columns if c in ['comment', 'comments', 'description', 'remark']), 'comment')

        # Check critical columns
        if not name_col or not email_col:
            missing = []
            if not name_col: missing.append("Name")
            if not email_col: missing.append("Email")
            messages.error(request, f"Missing required columns: {', '.join(missing)}. Please check your file headers.")
            return False

        added_count = 0
        skipped_count = 0
        
        # Use transaction to ensure all-or-nothing (Atomicity)
        with transaction.atomic():
            for _, row in df.iterrows():
                name = row[name_col]
                email = row[email_col]
                
                # Get optional fields safely
                category = row[category_col] if category_col in df.columns else 'N/A'
                comments = row[comment_col] if comment_col in df.columns else ''

                # Handle NaN/None
                if pd.isna(category): category = 'N/A'
                if pd.isna(comments): comments = ''
                
                if not Receipent.objects.filter(Sender=user, email=email).exists() and is_validEmail(str(email)):
                    Receipent.objects.create(
                        Sender=user,
                        name=name,
                        email=email,
                        receipent_category=category,   
                        comment=comments,              
                        source=f"File - {file.file_name}",
                        group=group
                    )
                    added_count += 1
                else:
                    skipped_count += 1
        
        messages.success(request, f"{added_count} recipients added successfully, {skipped_count} skipped.")
    
    except Exception as e:
        logger.error(f"Error processing file content: {e}")
        messages.error(request, f"Error processing file. Ensure correct format. {e}")
        return False

    return True


