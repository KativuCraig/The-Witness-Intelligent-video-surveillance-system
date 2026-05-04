#!/usr/bin/env python3
"""
GodsEye live worker: same loop as ``manage.py run_live_stream``, without going through Django's
management command loader.

Usage (from this project directory — the folder that contains ``manage.py``)::

    python scripts/run_live_worker.py <video_source_id> [--max-fps 3]

Or from anywhere, if you set PYTHONPATH to that directory::

    set PYTHONPATH=C:\\path\\to\\gods_eye
    python C:\\path\\to\\gods_eye\\scripts\\run_live_worker.py 1

Requires: ``VideoSource`` with ``source_type=LIVE`` and a valid ``stream_url``.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="GodsEye live RTSP/MJPEG worker (v2 models)")
    parser.add_argument("video_source_id", type=int, help="VideoSource database id")
    parser.add_argument("--max-fps", type=float, default=3.0, help="Score at most this many frames per second")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gods_eye.settings")

    import django

    django.setup()

    from detection.processing import run_live_stream_worker

    ok, err = run_live_stream_worker(args.video_source_id, max_fps=args.max_fps)
    if not ok and err:
        print(err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
