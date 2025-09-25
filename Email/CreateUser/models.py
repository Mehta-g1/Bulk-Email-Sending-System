from django.db import models
from datetime import datetime

# Create your models here.


class emailUsers(models.Model):
    name = models.CharField(max_length=100)
    email_address = models.EmailField(unique=True)
    email_password = models.CharField(max_length=200,null=True)   
    email_host = models.CharField(max_length=100, default="smtp.gmail.com")
    email_port = models.IntegerField(default=587,null=True)
    use_tls = models.BooleanField(default=True)
    login_password = models.CharField(max_length=50, null=False, default="test1234")

    # Disignation info
    org_name = models.CharField(max_length=150, null=True)
    post = models.CharField(max_length=100, null=True)
    department = models.CharField(max_length=150, null=True)
    about_you = models.CharField(max_length=500, null=True, default='')

    # Personal info
    image = models.ImageField(upload_to='images/',null=True)
    personalEmail = models.EmailField(null=True)
    dob = models.DateField( null=True)
    address = models.CharField(max_length=500, default='', null=True)
    phone = models.CharField(max_length=15, null=True)


    def __str__(self):
        return f"{self.name}   -{self.email_address}"

class UserFiles(models.Model):
    user = models.ForeignKey(emailUsers, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=200, null=False)
    file_size = models.CharField(max_length=50, null=False)
    file_type = models.CharField(max_length=50, null=False)
    file = models.FileField(upload_to='Receipients_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name}   -{self.file.name}"


class Receipent(models.Model):
    Sender = models.ForeignKey(emailUsers, on_delete=models.CASCADE)
    email = models.CharField(max_length=200, null=False, unique=False)
    name = models.CharField(max_length=150, null=False, default="Customer")
    receipent_category = models.CharField(max_length=100, null=True)
    comment = models.CharField(max_length=200, null=True)
    added_date = models.DateTimeField(auto_now=True)
    send_time = models.IntegerField(default=0)
    source = models.CharField(max_length=100, null=True, default="N/A")
    def __str__(self):
        return f"{self.name}   -{self.email}"

class reset_link(models.Model):
    user = models.ForeignKey(emailUsers, on_delete=models.CASCADE)
    token = models.CharField(max_length=50, null=True)
    datetime = models.DateTimeField(default=datetime.now)
    new_password = models.CharField(max_length=20, null=True)
    is_attempted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.name}  -Date: {self.datetime} - Token: {self.token}"
    

