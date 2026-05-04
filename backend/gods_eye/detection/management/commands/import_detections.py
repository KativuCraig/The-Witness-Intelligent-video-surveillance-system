import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from cameras.models import VideoSource
from incidents.models import Incident
from media_store.models import Evidence
from alerts.models import Alert
from accounts.models import User
from django.conf import settings


class Command(BaseCommand):
    help = "Import detections from a JSON file and create Incident/Evidence/Alert records"

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to detections JSON')
        parser.add_argument('--video-source-id', type=int, required=True, help='ID of VideoSource to associate')
        parser.add_argument('--fps', type=float, default=25.0, help='Frames per second of the source video (used to compute timestamps)')

    def handle(self, *args, **options):
        json_path = Path(options['json_file'])
        video_source_id = options['video_source_id']
        fps = float(options.get('fps', 25.0))

        if not json_path.exists():
            raise CommandError(f'JSON file not found: {json_path}')

        try:
            video_source = VideoSource.objects.get(id=video_source_id)
        except VideoSource.DoesNotExist:
            raise CommandError(f'VideoSource with id {video_source_id} not found')

        with json_path.open('r', encoding='utf-8') as f:
            data = json.load(f)

        created = 0
        for item in data:
            frame_index = item.get('frame_index')
            boxes = item.get('boxes', []) or []
            if not boxes:
                continue

            # pick highest-confidence box
            best = max(boxes, key=lambda b: float(b.get('conf', 0.0)))
            conf = float(best.get('conf', 0.0))
            cls = best.get('class')

            # map class id -> label using settings.YOLO_LABELS if present
            labels = list(getattr(settings, 'YOLO_LABELS', []))
            if labels and isinstance(cls, int) and 0 <= cls < len(labels):
                label = labels[cls]
            else:
                label = str(cls)

            # Create Incident
            incident = Incident.objects.create(
                video_source=video_source,
                incident_type=label,
                confidence=conf,
                detected_at=timezone.now()
            )

            # Create Evidence with timestamp computed from FPS
            timestamp = float(frame_index) / fps if fps > 0 else 0.0
            Evidence.objects.create(
                incident=incident,
                timestamp=timestamp
            )

            # Alert stakeholders (users with role SECURITY)
            users = User.objects.filter(role='SECURITY')
            for user in users:
                Alert.objects.create(
                    incident=incident,
                    user=user
                )

            created += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {created} incidents from {json_path}'))
