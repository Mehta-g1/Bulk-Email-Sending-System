from django.core.mail import EmailMessage, get_connection
from .models import emailUsers, Receipent


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