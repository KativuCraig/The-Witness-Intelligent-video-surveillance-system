from django.db import models
from cameras.models import VideoSource


class Incident(models.Model):
    """
    Stores detected suspicious activities.
    """

    INCIDENT_TYPE_CHOICES = (
        ('VIOLENCE', 'Violence'),
        ('WEAPON', 'Weapon Possession'),
        ('THEFT', 'Theft'),
    )

    STATUS_CHOICES = (
        ('NEW', 'New'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('RESOLVED', 'Resolved'),
    )

    video_source = models.ForeignKey(
        VideoSource,
        on_delete=models.CASCADE,
        related_name='incidents'
    )

    incident_type = models.CharField(
        max_length=20,
        choices=INCIDENT_TYPE_CHOICES
    )

    confidence = models.FloatField(
        help_text="Model confidence score"
    )

    detected_at = models.DateTimeField(
        help_text="Timestamp in video when incident occurred"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NEW'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.incident_type} - {self.video_source.name}"
