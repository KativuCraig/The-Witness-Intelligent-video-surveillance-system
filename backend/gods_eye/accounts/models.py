from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model to support roles for alerting and access control.
    """

    ROLE_CHOICES = (
        ('ADMIN', 'Administrator'),
        ('SECURITY', 'Security Officer'),
        ('VIEWER', 'Viewer'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='VIEWER'
    )

    fcm_device_token = models.TextField(
        blank=True,
        default='',
        help_text='FCM registration token for the companion mobile app (push alerts)',
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
