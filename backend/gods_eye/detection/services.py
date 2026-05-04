from collections import deque

from django.conf import settings
from django.utils import timezone

from accounts.models import User
from alerts.fcm import send_incident_push
from alerts.models import Alert
from incidents.models import Incident
from media_store.models import Evidence

# Legacy path-based detector (MOCK / single YOLO) for code that still imports DetectorClass.
try:
    if getattr(settings, "DETECTOR", "MOCK") == "YOLO":
        from .yolov8_detector import YOLOv8CrimeDetector as DetectorClass
    else:
        from .mock_detector import MockCrimeDetector as DetectorClass
except Exception:
    from .mock_detector import MockCrimeDetector as DetectorClass


class DetectionService:
    """
    Runs GodsEye v2 on in-memory frames when a BGR numpy frame is supplied; otherwise MOCK.
    """

    def __init__(self):
        if hasattr(DetectorClass, "get_instance"):
            try:
                self._legacy_detector = DetectorClass.get_instance()
            except Exception:
                self._legacy_detector = DetectorClass()
        else:
            self._legacy_detector = DetectorClass()

    def process_frame(self, video_source, frame, timestamp: float):
        try:
            import numpy as np
        except ImportError:
            np = None

        if np is not None and isinstance(frame, np.ndarray):
            from .processing import _robbery_score_for_emit, emit_detection_incident
            from .v2_engine import build_annotated_frame, ensure_models, score_frame

            ok, _ = ensure_models()
            if not ok:
                return None

            s = score_frame(frame)
            if s.get("error"):
                return None

            weapon_boxes = s.get("weapon_boxes") or []
            violence_boxes = s.get("violence_boxes") or []
            robbery_p = float(s.get("robbery_p", 0.0))
            weapon_top = float(s.get("weapon_top_conf", 0.0))
            violence_top = float(s.get("violence_top_conf", s.get("violence_p", 0.0)))

            v_thr = float(getattr(settings, "GODEYE_V2_VIOLENCE_INCIDENT_CONF", 0.35))
            r_thr = float(getattr(settings, "GODEYE_V2_ROBBERY_CONF", 0.72))
            w_thr = float(getattr(settings, "GODEYE_V2_WEAPON_INCIDENT_CONF", 0.35))
            min_gap = float(getattr(settings, "GODEYE_MIN_SECONDS_BETWEEN_INCIDENTS", 12.0))
            rb_smooth = bool(getattr(settings, "GODEYE_V2_ROBBERY_TEMPORAL_SMOOTH", True))
            rb_win = max(2, int(getattr(settings, "GODEYE_V2_ROBBERY_SMOOTH_WINDOW", 8)))
            rb_min_s = max(1, int(getattr(settings, "GODEYE_V2_ROBBERY_SMOOTH_MIN_SAMPLES", 5)))
            rb_min_peak = float(getattr(settings, "GODEYE_V2_ROBBERY_SMOOTH_MIN_PEAK", 0.58))
            theft_alerts_enabled = bool(getattr(settings, "GODEYE_V2_ENABLE_THEFT_ALERTS", False))

            buf = getattr(video_source, "_robbery_emit_buf", None)
            if buf is None or getattr(buf, "maxlen", None) != rb_win:
                buf = deque(maxlen=rb_win)
                video_source._robbery_emit_buf = buf
            r_score, r_ok = _robbery_score_for_emit(
                robbery_p,
                buf,
                temporal_smooth=rb_smooth,
                smooth_min_samples=rb_min_s,
                min_peak_raw=rb_min_peak,
                append_sample=True,
            )

            annotated = build_annotated_frame(frame, weapon_boxes, violence_boxes, robbery_p)
            last_emit_times: dict[str, float] = {}
            last_emit_times.update(getattr(video_source, "_v2_debounce_times", {}) or {})

            created = None
            if weapon_top >= w_thr:
                inc = emit_detection_incident(
                    vs=video_source,
                    evidence_bgr=annotated,
                    video_time=float(timestamp),
                    incident_type="WEAPON",
                    confidence=weapon_top,
                    last_emit_times=last_emit_times,
                    min_gap=min_gap,
                )
                if inc is not None:
                    created = inc
            if violence_top >= v_thr:
                inc = emit_detection_incident(
                    vs=video_source,
                    evidence_bgr=annotated,
                    video_time=float(timestamp),
                    incident_type="VIOLENCE",
                    confidence=violence_top,
                    last_emit_times=last_emit_times,
                    min_gap=min_gap,
                )
                if inc is not None:
                    created = inc
            if theft_alerts_enabled and r_ok and r_score >= r_thr:
                inc = emit_detection_incident(
                    vs=video_source,
                    evidence_bgr=annotated,
                    video_time=float(timestamp),
                    incident_type="THEFT",
                    confidence=float(r_score),
                    last_emit_times=last_emit_times,
                    min_gap=min_gap,
                )
                if inc is not None:
                    created = inc

            video_source._v2_debounce_times = last_emit_times
            return created

        result = self._legacy_detector.analyze_frame(frame, timestamp)

        if result.label is None:
            return None

        incident = Incident.objects.create(
            video_source=video_source,
            incident_type=result.label,
            confidence=result.confidence,
            detected_at=timezone.now(),
        )

        Evidence.objects.create(incident=incident, timestamp=result.timestamp)

        for user in User.objects.filter(role="SECURITY"):
            alert = Alert.objects.create(incident=incident, user=user)
            send_incident_push(alert)

        return incident
