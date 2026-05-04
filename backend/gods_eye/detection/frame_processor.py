import time
from .services import DetectionService


class FrameProcessor:
    """
    Simulates frame extraction from video sources.
    """

    def __init__(self, video_source):
        self.video_source = video_source
        self.detection_service = DetectionService()

    def run(self, duration_seconds=60, interval=5):
        """
        Simulate processing frames every `interval` seconds.
        """

        current_time = 0

        while current_time <= duration_seconds:
            fake_frame = None  # placeholder
            self.detection_service.process_frame(
                self.video_source,
                fake_frame,
                timestamp=current_time
            )

            time.sleep(0.1)
            current_time += interval
