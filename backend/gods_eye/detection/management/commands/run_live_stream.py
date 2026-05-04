"""
Run GodsEye v2 on a LIVE VideoSource (RTSP/MJPEG).

Thin wrapper around ``detection.processing.run_live_stream_worker``.
Also runnable as a plain script: ``python scripts/run_live_worker.py ...``.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from detection.processing import run_live_stream_worker


class Command(BaseCommand):
    help = "Run GodsEye v2 on a LIVE VideoSource (RTSP/MJPEG stream_url)"

    def add_arguments(self, parser):
        parser.add_argument("video_source_id", type=int, help="VideoSource id (source_type=LIVE)")
        parser.add_argument(
            "--max-fps",
            type=float,
            default=3.0,
            help="Soft cap on how many frames per second to score (reduces CPU/GPU load)",
        )

    def handle(self, *args, **options):
        vid = options["video_source_id"]
        max_fps = float(options["max_fps"])

        def _log(msg: str) -> None:
            self.stdout.write(msg)

        ok, err = run_live_stream_worker(vid, max_fps=max_fps, log=_log)
        if not ok and err:
            self.stderr.write(self.style.ERROR(err))
