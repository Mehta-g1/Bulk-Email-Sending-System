from django.db import models
from django.utils import timezone
from datetime import timedelta


class OTPVerification(models.Model):
    PURPOSE_CHOICES = [
        ('login', 'Login'),
        ('register', 'Register'),
        ('api', 'API'),
        ('general', 'General'),
    ]

    email = models.EmailField(db_index=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='general')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_verified']),
        ]

    def save(self, *args, **kwargs):
        if not self.pk:
            # Auto-set expiry to 10 minutes from now
            self.expiry_time = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expiry_time

    def is_max_attempts(self):
        return self.attempts >= 5

    def __str__(self):
        status = 'verified' if self.is_verified else ('expired' if self.is_expired() else 'active')
        return f"OTP[{status}] → {self.email} ({self.purpose})"
