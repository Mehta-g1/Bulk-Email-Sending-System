from django.db import models


# Create your models here.


class emailUsers(models.Model):
    name = models.CharField(max_length=100)
    email_address = models.EmailField(unique=True)
    email_password = models.CharField(max_length=200)   # ⚠️ Plain text me mat rakho
    email_host = models.CharField(max_length=100, default="smtp.gmail.com")
    email_port = models.IntegerField(default=587)
    use_tls = models.BooleanField(default=True)
    login_password = models.CharField(max_length=50, null=False, default="test1234")


    def __str__(self):
        return f"{self.name}   -{self.email_address}"
    

class Receipent(models.Model):
    Sender = models.ForeignKey(emailUsers, on_delete=models.CASCADE)
    email = models.CharField(max_length=200, null=False, unique=False)
    name = models.CharField(max_length=150, null=False, default="Customer")

    def __str__(self):
        return f"{self.name}   -{self.email}"