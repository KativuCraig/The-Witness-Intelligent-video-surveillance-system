from __future__ import annotations

import logging
import signal
import threading
import time
from collections import deque
from collections.abc import Callable
from typing import Optional

import cv2
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from accounts.models import User
from alerts.fcm import send_incident_push
from alerts.models import Alert
from cameras.models import VideoSource
from incidents.models import Incident
from media_store.models import Evidence

from .live_stream_urls import live_http_candidate_urls
from .v2_engine import (
    build_annotated_frame,
    ensure_models,
    robbery_on_frame,
    violence_on_frame,
    weapon_on_frame,
)

logger = logging.getLogger(__name__)


def _robbery_score_for_emit(
    robbery_raw: float,
    buf: deque,
    *,
    temporal_smooth: bool,
    smooth_min_samples: int,
    min_peak_raw: float,
    append_sample: bool,
) -> tuple[float, bool]:
    """
    Reduce false THEFT (robbery cls) alerts.

    When ``temporal_smooth`` is True, uses a rolling mean over recent classifier
    samples and requires at least one sample above ``min_peak_raw`` (dampens
    single-frame spikes that still show high softmax).

    Returns ``(score, eligible)`` — compare ``score`` to ``GODEYE_V2_ROBBERY_CONF``
    only when ``eligible`` is True.
    """
    if not temporal_smooth:
        return (float(robbery_raw), append_sample)

    if append_sample:
        buf.append(float(robbery_raw))
    if len(buf) < smooth_min_samples:
        return (0.0, False)
    mean_p = sum(buf) / len(buf)
    if max(buf) < min_peak_raw:
        return (mean_p, False)
    return (mean_p, True)


def emit_detection_incident(
    *,
    vs: VideoSource,
    evidence_bgr,
    video_time: float,
    incident_type: str,
    confidence: float,
    last_emit_times: dict,
    min_gap: float,
) -> Optional[Incident]:
    """
    Create Incident, persist annotated evidence image, notify SECURITY users (FCM).

    Returns the new Incident when created, else None (debounce or invalid type).
    """
    valid = {c[0] for c in Incident.INCIDENT_TYPE_CHOICES}
    if incident_type not in valid:
        logger.debug("Skip unknown incident_type %s", incident_type)
        return None
    # Demo safety switch: block THEFT emission globally when disabled.
    if incident_type == "THEFT" and not bool(getattr(settings, "GODEYE_V2_ENABLE_THEFT_ALERTS", False)):
        logger.debug("Skip THEFT incident because GODEYE_V2_ENABLE_THEFT_ALERTS is disabled")
        return None
    prev = last_emit_times.get(incident_type, -1e9)
    if video_time - prev < min_gap:
        return None
    last_emit_times[incident_type] = video_time

    incident = Incident.objects.create(
        video_source=vs,
        incident_type=incident_type,
        confidence=confidence,
        detected_at=timezone.now(),
    )

    if evidence_bgr is not None:
        success, encoded = cv2.imencode(".jpg", evidence_bgr)
        if success:
            content = ContentFile(encoded.tobytes())
            filename = f"frames/{vs.id}_{int(time.time())}_{incident.id}.jpg"
            evidence = Evidence(incident=incident, timestamp=video_time)
            evidence.image_frame.save(filename, content, save=True)
        else:
            Evidence.objects.create(incident=incident, timestamp=video_time)
    else:
        Evidence.objects.create(incident=incident, timestamp=video_time)

    for user in User.objects.filter(role="SECURITY"):
        alert = Alert.objects.create(incident=incident, user=user)
        send_incident_push(alert)

    return incident


def run_live_stream_worker(
    video_source_id: int,
    *,
    max_fps: float = 3.0,
    log: Optional[Callable[[str], None]] = None,
) -> tuple[bool, Optional[str]]:
    """
    Blocking loop: read ``VideoSource.stream_url`` (RTSP/MJPEG), run v2 models, emit incidents.

    Use from a standalone script (after ``django.setup()``) or from ``run_live_stream`` command.
    Returns ``(True, None)`` on normal stop (Ctrl+C), or ``(False, error)`` on fatal setup/open errors.
    """
    _log = log or (lambda m: print(m, flush=True))

    vs = VideoSource.objects.filter(id=video_source_id).first()
    if not vs:
        return False, f"No VideoSource with id={video_source_id}"
    if vs.source_type != "LIVE":
        return False, "VideoSource must have source_type=LIVE"
    url = (vs.stream_url or "").strip()
    if not url:
        return False, "stream_url is empty"

    ok, err = ensure_models()
    if not ok:
        return False, err or "v2 models failed to load"

    max_fps = max(0.1, float(max_fps))
    frame_interval = 1.0 / max_fps

    min_gap = float(getattr(settings, "GODEYE_MIN_SECONDS_BETWEEN_INCIDENTS", 12.0))
    cls_stride = max(1, int(getattr(settings, "GODEYE_V2_CLS_EVERY_N_FRAMES", 4)))
    v_stride = max(1, int(getattr(settings, "GODEYE_V2_VIOLENCE_EVERY_N_FRAMES", 1)))
    w_stride = max(1, int(getattr(settings, "GODEYE_V2_WEAPON_EVERY_N_FRAMES", 1)))
    v_thr = float(getattr(settings, "GODEYE_V2_VIOLENCE_INCIDENT_CONF", 0.35))
    r_thr = float(getattr(settings, "GODEYE_V2_ROBBERY_CONF", 0.72))
    w_thr = float(getattr(settings, "GODEYE_V2_WEAPON_INCIDENT_CONF", 0.35))
    min_conf = float(getattr(settings, "YOLO_CONFIDENCE_THRESHOLD", 0.25))
    rb_smooth = bool(getattr(settings, "GODEYE_V2_ROBBERY_TEMPORAL_SMOOTH", True))
    rb_win = max(2, int(getattr(settings, "GODEYE_V2_ROBBERY_SMOOTH_WINDOW", 8)))
    rb_min_s = max(1, int(getattr(settings, "GODEYE_V2_ROBBERY_SMOOTH_MIN_SAMPLES", 5)))
    rb_min_peak = float(getattr(settings, "GODEYE_V2_ROBBERY_SMOOTH_MIN_PEAK", 0.58))
    theft_alerts_enabled = bool(getattr(settings, "GODEYE_V2_ENABLE_THEFT_ALERTS", False))
    rb_buf: deque = deque(maxlen=rb_win)

    last_emit_times: dict[str, float] = {}
    stop = {"flag": False}

    def _stop(*_):
        stop["flag"] = True

    signal.signal(signal.SIGINT, _stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _stop)

    def _open_capture(u: str):
        c = cv2.VideoCapture(u, cv2.CAP_FFMPEG)
        try:
            c.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        return c

    _log(f"Saved stream URL: {url[:96]}...")
    _log(
        "IP Camera (iOS) / ShenYao: the app shows several links — use the MJPEG (browser) line, "
        "often http://IP:PORT/video , not only http://IP:PORT/ . Default admin/admin if auth is on: "
        "http://admin:admin@IP:PORT/video"
    )

    candidates = live_http_candidate_urls(url)
    working_url = None
    cap = None
    for u in candidates:
        c = _open_capture(u)
        if not c.isOpened():
            try:
                c.release()
            except Exception:
                pass
            continue
        ok_fr, frm = c.read()
        if ok_fr and frm is not None:
            working_url = u
            cap = c
            if u.rstrip("/") != url.rstrip("/"):
                _log(f"Using working URL: {u} (saved URL had no MJPEG path; auto-tried common paths)")
            break
        try:
            c.release()
        except Exception:
            pass

    if not working_url or cap is None:
        return (
            False,
            "Could not open stream or read a frame. For «IP Camera» on iOS, copy the MJPEG address "
            "from the app (often ends with /video). If login is enabled, include user:pass@ in the URL.",
        )

    frame_index = 0
    wall_origin = time.monotonic()
    reconnect_delay = 1.0
    reconnect_cap = 20.0
    _log("Streaming — Ctrl+C to stop")

    try:
        while not stop["flag"]:
            t_loop = time.monotonic()
            ret, frame = cap.read()
            if not ret or frame is None:
                try:
                    cap.release()
                except Exception:
                    pass
                _log(
                    f"Stream interrupted (app closed the HTTP connection, wrong URL, or network). "
                    f"Retrying in {reconnect_delay:.1f}s…"
                )
                time.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 1.35, reconnect_cap)
                cap = _open_capture(working_url)
                if not cap.isOpened():
                    _log("Could not reopen yet; will keep retrying (phone asleep, Wi‑Fi, or server stopped).")
                    continue
                reconnect_delay = 1.0
                continue

            reconnect_delay = 1.0

            video_time = time.monotonic() - wall_origin

            if frame_index % w_stride == 0:
                weapon_boxes, weapon_top = weapon_on_frame(frame)
            else:
                weapon_boxes, weapon_top = [], 0.0

            if frame_index % v_stride == 0:
                violence_boxes, violence_top = violence_on_frame(frame)
            else:
                violence_boxes, violence_top = [], 0.0

            if frame_index % cls_stride == 0:
                robbery_p = robbery_on_frame(frame)
            else:
                robbery_p = 0.0

            annotated = build_annotated_frame(frame, weapon_boxes, violence_boxes, robbery_p)

            if weapon_top >= max(min_conf, w_thr):
                emit_detection_incident(
                    vs=vs,
                    evidence_bgr=annotated,
                    video_time=video_time,
                    incident_type="WEAPON",
                    confidence=float(weapon_top),
                    last_emit_times=last_emit_times,
                    min_gap=min_gap,
                )
            if violence_top >= max(min_conf, v_thr):
                emit_detection_incident(
                    vs=vs,
                    evidence_bgr=annotated,
                    video_time=video_time,
                    incident_type="VIOLENCE",
                    confidence=float(violence_top),
                    last_emit_times=last_emit_times,
                    min_gap=min_gap,
                )
            r_score, r_ok = _robbery_score_for_emit(
                robbery_p,
                rb_buf,
                temporal_smooth=rb_smooth,
                smooth_min_samples=rb_min_s,
                min_peak_raw=rb_min_peak,
                append_sample=(frame_index % cls_stride == 0),
            )
            if theft_alerts_enabled and r_ok and r_score >= r_thr:
                emit_detection_incident(
                    vs=vs,
                    evidence_bgr=annotated,
                    video_time=video_time,
                    incident_type="THEFT",
                    confidence=float(r_score),
                    last_emit_times=last_emit_times,
                    min_gap=min_gap,
                )

            frame_index += 1
            elapsed = time.monotonic() - t_loop
            sleep_for = frame_interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)
    finally:
        cap.release()

    _log("Stopped.")
    return True, None


def process_uploaded_video(
    video_source_id: int,
    video_path: str,
    min_conf: float = 0.25,
    save_annotated_preview: bool = True,
    fps: float | None = None,
):
    """
    Final GodsEye models (``models/v2/``):

    - **WEAPON**: YOLO detect ``weapon_detect_robust_v1``
    - **VIOLENCE**: YOLO detect ``violence_model2``
    - **THEFT** (robbery): YOLO-cls ``robbery_v2_ft2`` → ``Incident.incident_type == THEFT``

    Objectives:
    1) Annotated frames on ``Evidence`` for security review
    2) FCM alerts to SECURITY-role users (companion app)
    3) Debounced cadence via ``GODEYE_MIN_SECONDS_BETWEEN_INCIDENTS`` (~10–15s style)
    """
    vs = VideoSource.objects.filter(id=video_source_id).first()
    if not vs:
        return None

    ok, err = ensure_models()
    if not ok:
        return {"created_incidents": 0, "annotated_preview": None, "error": err}

    min_gap = float(getattr(settings, "GODEYE_MIN_SECONDS_BETWEEN_INCIDENTS", 12.0))
    cls_stride = max(1, int(getattr(settings, "GODEYE_V2_CLS_EVERY_N_FRAMES", 4)))
    v_stride = max(1, int(getattr(settings, "GODEYE_V2_VIOLENCE_EVERY_N_FRAMES", 1)))
    w_stride = max(1, int(getattr(settings, "GODEYE_V2_WEAPON_EVERY_N_FRAMES", 1)))

    v_thr = float(getattr(settings, "GODEYE_V2_VIOLENCE_INCIDENT_CONF", 0.35))
    r_thr = float(getattr(settings, "GODEYE_V2_ROBBERY_CONF", 0.72))
    w_thr = float(getattr(settings, "GODEYE_V2_WEAPON_INCIDENT_CONF", 0.35))
    rb_smooth = bool(getattr(settings, "GODEYE_V2_ROBBERY_TEMPORAL_SMOOTH", True))
    rb_win = max(2, int(getattr(settings, "GODEYE_V2_ROBBERY_SMOOTH_WINDOW", 8)))
    rb_min_s = max(1, int(getattr(settings, "GODEYE_V2_ROBBERY_SMOOTH_MIN_SAMPLES", 5)))
    rb_min_peak = float(getattr(settings, "GODEYE_V2_ROBBERY_SMOOTH_MIN_PEAK", 0.58))
    theft_alerts_enabled = bool(getattr(settings, "GODEYE_V2_ENABLE_THEFT_ALERTS", False))
    rb_buf: deque = deque(maxlen=rb_win)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {"created_incidents": 0, "annotated_preview": None, "error": "Could not open video"}

    actual_fps = fps if fps is not None else cap.get(cv2.CAP_PROP_FPS) or 25.0
    last_emit_times: dict[str, float] = {}
    created = 0
    last_preview_bgr = None
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        video_time = float(frame_index) / float(actual_fps) if actual_fps > 0 else 0.0

        if frame_index % w_stride == 0:
            weapon_boxes, weapon_top = weapon_on_frame(frame)
        else:
            weapon_boxes, weapon_top = [], 0.0

        if frame_index % v_stride == 0:
            violence_boxes, violence_top = violence_on_frame(frame)
        else:
            violence_boxes, violence_top = [], 0.0

        if frame_index % cls_stride == 0:
            robbery_p = robbery_on_frame(frame)
        else:
            robbery_p = 0.0

        annotated = build_annotated_frame(frame, weapon_boxes, violence_boxes, robbery_p)
        last_preview_bgr = annotated

        if weapon_top >= max(min_conf, w_thr):
            if emit_detection_incident(
                vs=vs,
                evidence_bgr=annotated,
                video_time=video_time,
                incident_type="WEAPON",
                confidence=float(weapon_top),
                last_emit_times=last_emit_times,
                min_gap=min_gap,
            ):
                created += 1

        if violence_top >= max(min_conf, v_thr):
            if emit_detection_incident(
                vs=vs,
                evidence_bgr=annotated,
                video_time=video_time,
                incident_type="VIOLENCE",
                confidence=float(violence_top),
                last_emit_times=last_emit_times,
                min_gap=min_gap,
            ):
                created += 1

        r_score, r_ok = _robbery_score_for_emit(
            robbery_p,
            rb_buf,
            temporal_smooth=rb_smooth,
            smooth_min_samples=rb_min_s,
            min_peak_raw=rb_min_peak,
            append_sample=(frame_index % cls_stride == 0),
        )
        if theft_alerts_enabled and r_ok and r_score >= r_thr:
            if emit_detection_incident(
                vs=vs,
                evidence_bgr=annotated,
                video_time=video_time,
                incident_type="THEFT",
                confidence=float(r_score),
                last_emit_times=last_emit_times,
                min_gap=min_gap,
            ):
                created += 1

        frame_index += 1

    cap.release()

    preview_path = None
    if save_annotated_preview and last_preview_bgr is not None and hasattr(vs, "processed_file"):
        try:
            ok_enc, buf = cv2.imencode(".jpg", last_preview_bgr)
            if ok_enc:
                dest_name = f"annotated/{vs.id}_{int(time.time())}_preview.jpg"
                vs.processed_file.save(dest_name, ContentFile(buf.tobytes()), save=True)
                preview_path = vs.processed_file.name
        except Exception:
            logger.exception("Could not save annotated preview on VideoSource")

    return {"created_incidents": created, "annotated_preview": preview_path}


def process_uploaded_video_async(video_source_id: int, video_path: str, **kwargs):
    thread = threading.Thread(
        target=process_uploaded_video,
        args=(video_source_id, video_path),
        kwargs=kwargs,
        daemon=True,
    )
    thread.start()
    return thread
