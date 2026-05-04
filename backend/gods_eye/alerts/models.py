from django.db import models
from incidents.models import Incident
from accounts.models import User


class Alert(models.Model):
    """
    Records alerts sent to stakeholders.
    """

    DELIVERY_STATUS_CHOICES = (
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed'),
    )

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='alerts'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='alerts'
    )

    sent_at = models.DateTimeField(auto_now_add=True)

    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default='SENT'
    )

    def __str__(self):
        return f"Alert to {self.user.username} - {self.incident.id}"
