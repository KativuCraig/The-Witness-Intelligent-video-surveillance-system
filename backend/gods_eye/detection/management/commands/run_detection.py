from django.core.management.base import BaseCommand
from cameras.models import VideoSource
from detection.frame_processor import FrameProcessor


class Command(BaseCommand):
    help = "Run mock detection on a video source"

    def add_arguments(self, parser):
        parser.add_argument('video_source_id', type=int)

    def handle(self, *args, **options):
        video_source = VideoSource.objects.get(id=options['video_source_id'])

        processor = FrameProcessor(video_source)
        processor.run()

        self.stdout.write(self.style.SUCCESS("Detection completed"))
