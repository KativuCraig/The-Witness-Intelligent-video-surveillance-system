from pathlib import Path
import threading
from typing import Optional

from django.conf import settings
import numpy as np

from .base import BaseCrimeDetector
from .contracts import DetectionResult


class YOLOv8CrimeDetector(BaseCrimeDetector):
    """
    YOLOv8-based detector that returns a single DetectionResult (the highest-confidence
    detection) or no detection.

    This is intentionally conservative: it maps the top detection to the existing
    `DetectionResult` shape used elsewhere in the project. It uses a singleton
    loader so the model is loaded only once per process.
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self, weights_path: Optional[str] = None):
        # lazy import heavy libs so module import stays cheap
        try:
            from ultralytics import YOLO
        except Exception as e:
            raise ImportError("ultralytics is required for YOLOv8 detector: " + str(e))

        self._YOLO = YOLO

        # decide weights path
        if weights_path:
            self.weights = Path(weights_path)
        else:
            self.weights = Path(getattr(settings, 'YOLO_WEIGHTS', Path('models') / 'best.pt'))

        # device: prefer CUDA if available
        try:
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        except Exception:
            device = 'cpu'

        # instantiate model
        self.model = self._YOLO(str(self.weights))
        # store config defaults
        self.imgsz = getattr(settings, 'YOLO_IMGSZ', 640)
        self.conf = float(getattr(settings, 'YOLO_CONFIDENCE_THRESHOLD', 0.25))
        self.labels = list(getattr(settings, 'YOLO_LABELS', ['VIOLENCE', 'WEAPON', 'THEFT']))

    @classmethod
    def get_instance(cls, weights_path: Optional[str] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = YOLOv8CrimeDetector(weights_path=weights_path)
        return cls._instance

    def analyze_frame(self, frame, timestamp: float) -> DetectionResult:
        """
        frame can be:
          - a numpy array (H,W,3) in BGR or RGB (we pass through to ultralytics)
          - a path to an image file (string / Path)
          - None -> returns no detection

        Returns a DetectionResult representing the highest-confidence detection
        or a result with label=None when nothing is detected.
        """

        if frame is None:
            return DetectionResult(label=None, confidence=0.0, timestamp=timestamp, frame_path=None)

        # run inference
        try:
            # ultralytics accepts numpy arrays and file paths
            results = self.model.predict(source=frame, imgsz=self.imgsz, conf=self.conf, verbose=False)
        except Exception as e:
            # on any inference error, return no detection (caller may log)
            return DetectionResult(label=None, confidence=0.0, timestamp=timestamp, frame_path=None)

        # results is a list-like; we use first item
        if not results or len(results) == 0:
            return DetectionResult(label=None, confidence=0.0, timestamp=timestamp, frame_path=None)

        r = results[0]
        boxes = getattr(r, 'boxes', None)
        if not boxes or len(boxes) == 0:
            return DetectionResult(label=None, confidence=0.0, timestamp=timestamp, frame_path=None)

        # find box with max confidence
        best_box = None
        best_conf = -1.0
        best_cls = None
        for b in boxes:
            try:
                conf = float(b.conf.cpu().numpy()[0]) if hasattr(b.conf, 'cpu') else float(b.conf[0])
            except Exception:
                # fallback if conf is already a float or list
                try:
                    conf = float(b.conf[0])
                except Exception:
                    conf = float(b.conf)

            if conf > best_conf:
                best_conf = conf
                best_box = b
                try:
                    best_cls = int(b.cls.cpu().numpy()[0]) if hasattr(b.cls, 'cpu') else int(b.cls[0])
                except Exception:
                    try:
                        best_cls = int(b.cls[0])
                    except Exception:
                        best_cls = int(b.cls)

        if best_conf <= 0 or best_box is None:
            return DetectionResult(label=None, confidence=0.0, timestamp=timestamp, frame_path=None)

        # map class id to label if available
        label = None
        if best_cls is not None and 0 <= best_cls < len(self.labels):
            label = self.labels[best_cls]
        else:
            label = str(best_cls)

        return DetectionResult(label=label, confidence=float(best_conf), timestamp=timestamp, frame_path=None)
