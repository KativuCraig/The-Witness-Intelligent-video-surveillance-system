from django.db import models


class VideoSource(models.Model):
    """
    Represents either a live CCTV feed or an uploaded video.
    """

    SOURCE_TYPE_CHOICES = (
        ('LIVE', 'Live Camera'),
        ('UPLOAD', 'Uploaded Video'),
    )

    name = models.CharField(max_length=255)

    source_type = models.CharField(
        max_length=10,
        choices=SOURCE_TYPE_CHOICES
    )

    stream_url = models.URLField(
        blank=True,
        null=True,
        help_text="RTSP/HTTP URL for live cameras"
    )

    video_file = models.FileField(
        upload_to='videos/',
        blank=True,
        null=True,
        help_text="Uploaded video file"
    )

    # Processed annotated output (set after processing completes)
    processed_file = models.FileField(
        upload_to='annotated/',
        blank=True,
        null=True,
        help_text="Processed / annotated video file"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.source_type})"
