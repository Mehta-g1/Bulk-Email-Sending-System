from django.db import models
from CreateUser.models import emailUsers


class Template(models.Model):
    template_name = models.CharField(max_length=100)
    user = models.ForeignKey(emailUsers, on_delete=models.CASCADE)
    subject = models.CharField(max_length=500, null=True)
    body = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateField(null=True, auto_now=True)
    primary = models.BooleanField(default=False)
    no_of_time_used = models.IntegerField(default=0)
    def __str__(self):

        return f" {self.id}  -{self.user.name}  -{self.template_name} -{self.created_at}"