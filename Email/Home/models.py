from django.db import models

# Create your models here.
class Contact(models.Model):
    USER_TYPE_CHOICES = [
        ('registered', 'Registered Customer'),
        ('unregistered', 'Unregistered Customer'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    email = models.EmailField()
    query = models.TextField()
    suggestion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
