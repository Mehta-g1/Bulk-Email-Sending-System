from django.core.mail import EmailMessage, get_connection, send_mail
from .models import emailUsers, Receipent, reset_link
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import get_object_or_404

def getReceipentList(user_id):
    recipients = Receipent.objects.filter(Sender__id=user_id)
    r_list = [r.email for r in recipients]
    # print(r_list)
    return r_list


def send_bulk_email(user_id):
    account = emailUsers.objects.get(id=user_id)
    try:
        connection = get_connection(
            host=account.email_host,
            port=account.email_port,
            username=account.email_address,
            password=account.email_password,
            use_tls=account.use_tls,
        )

        # Email send
        email = EmailMessage(
            subject="Bulk Mail Test",
            body="Hello Clients! This mail is from " + account.name,
            from_email=account.email_address,
            to=getReceipentList(user_id),
            connection=connection,
        )
        email.send()
    except Exception as e:
        print('\n\n--------------------')
        print("Error:",e)
        print("---------------------\n\n")
        return False
    return True



def send_forget_password_link(user_email, token):
    """
    Sends a password reset link to the given user email.
    
    Parameters:
        user_email (str): The email address of the user who requested reset
        token (str): A unique reset token (generated in view)
    """

    # Reset link (example: http://127.0.0.1:8000/reset-password/<token>/)
    reset_link = f"http://127.0.0.1:8000/reset-password/{token}/"

    subject = "Reset Your Password"
    message = f"""
    We received a request to reset your password.

    Please click the link below to reset your password:
    {reset_link}

    If you did not request this, you can safely ignore this email.

    Thanks,
    Your Company Team
    """

    from_email = settings.DEFAULT_FROM_EMAIL  # use company noreply email
    recipient_list = [user_email]

    send_mail(subject, message, from_email, recipient_list)


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