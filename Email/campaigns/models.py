import uuid
from django.db import models
from CreateUser.models import emailUsers


class Campaign(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(emailUsers, on_delete=models.CASCADE, related_name='campaigns')
    campaign_name = models.CharField(max_length=255)
    subject = models.CharField(max_length=500, default='')
    total_emails = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    pending_count = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    template_id = models.IntegerField(null=True, blank=True)  # store template id reference
    email_body = models.TextField(null=True, blank=True)  # Store the actual body sent

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"[{self.status.upper()}] {self.campaign_name} - {self.user.name}"

    def update_stats(self):
        """Recalculate and save success_rate."""
        if self.total_emails > 0:
            self.success_rate = round((self.sent_count / self.total_emails) * 100, 2)
        else:
            self.success_rate = 0.0
        self.save(update_fields=['sent_count', 'failed_count', 'pending_count', 'success_rate', 'status'])


class EmailLog(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='logs')
    recipient_email = models.EmailField()
    recipient_name = models.CharField(max_length=200, default='Customer')
    subject = models.CharField(max_length=500)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    # Tracking fields
    tracking_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['tracking_id']),
            models.Index(fields=['recipient_email']),
        ]

    def __str__(self):
        return f"{self.recipient_email} → {self.status} ({self.campaign.campaign_name})"
