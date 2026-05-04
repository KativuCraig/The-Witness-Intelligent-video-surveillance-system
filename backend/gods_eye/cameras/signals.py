from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import threading

from .models import VideoSource
from detection.processing import process_uploaded_video_async


@receiver(post_save, sender=VideoSource)
def auto_process_uploaded_video(sender, instance: VideoSource, created, **kwargs):
    """
    When a VideoSource is saved with an uploaded file, start background processing.
    This is intentionally lightweight: it spawns a background thread so the request
    that saved the model is not blocked.

    Live RTSP (source_type=LIVE) is not auto-processed here yet; for 10–15s-lag live
    scanning, add a worker that reads bounded chunks from stream_url and calls the
    same detection helpers with a rolling buffer + stride.
    """
    try:
        # Only process uploaded videos
        if instance.source_type != 'UPLOAD':
            return

        # Ensure there is a file to process
        vf = getattr(instance, 'video_file', None)
        if not vf:
            return

        # Avoid double-processing if attribute set during runtime (best-effort)
        if getattr(instance, '_processing_started', False):
            return

        instance._processing_started = True

        video_path = vf.path if hasattr(vf, 'path') else vf.name

        # Start processing in background
        process_uploaded_video_async(instance.id, video_path, save_annotated_preview=True)
    except Exception:
        # swallow exceptions to avoid breaking save; logging can be added
        return
