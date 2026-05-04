import json
from pathlib import Path

import cv2
from django.core.management.base import BaseCommand

from detection.v2_engine import ensure_models, score_frame


class Command(BaseCommand):
    help = "Run GodsEye v2 models on a video and write per-frame scores to JSON"

    def add_arguments(self, parser):
        parser.add_argument("source", type=str, help="Path to video or image file")
        parser.add_argument("--out", type=str, default="inference_output.json", help="Output JSON file")
        parser.add_argument(
            "--sample",
            type=int,
            default=1,
            help="Process every Nth frame (1 = all frames)",
        )

    def handle(self, *args, **options):
        src = Path(options["source"])
        out_path = Path(options["out"])
        sample = max(1, int(options["sample"]))

        ok, err = ensure_models()
        if not ok:
            self.stderr.write(self.style.ERROR(err or "v2 models failed to load"))
            return

        cap = cv2.VideoCapture(str(src))
        if not cap.isOpened():
            self.stderr.write(self.style.ERROR(f"Could not open: {src}"))
            return

        output = []
        idx = 0
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            if idx % sample != 0:
                idx += 1
                continue
            s = score_frame(frame)
            wboxes = s.get("weapon_boxes") or []
            vboxes = s.get("violence_boxes") or []
            frame_info = {
                "frame_index": idx,
                "weapon_top_conf": s.get("weapon_top_conf", 0.0),
                "violence_top_conf": s.get("violence_top_conf", s.get("violence_p", 0.0)),
                "robbery_p": s.get("robbery_p", 0.0),
                "weapon_boxes": [{"xyxy": b.get("xyxy"), "conf": b.get("conf"), "label": b.get("label")} for b in wboxes],
                "violence_boxes": [{"xyxy": b.get("xyxy"), "conf": b.get("conf"), "label": b.get("label")} for b in vboxes],
            }
            if s.get("error"):
                frame_info["error"] = s["error"]
            output.append(frame_info)
            idx += 1

        cap.release()

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Inference complete, results written to {out_path}"))
