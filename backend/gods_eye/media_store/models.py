from django.db import models
from incidents.models import Incident


class Evidence(models.Model):
    """
    Stores captured frames or video snippets related to an incident.
    """

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='evidence'
    )

    image_frame = models.ImageField(
        upload_to='frames/',
        blank=True,
        null=True
    )

    video_snippet = models.FileField(
        upload_to='snippets/',
        blank=True,
        null=True
    )

    timestamp = models.FloatField(
        help_text="Second in video where frame/snippet was captured"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evidence for Incident {self.incident.id}"
