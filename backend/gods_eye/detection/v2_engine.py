"""
GodsEyeEngine final checkpoints (copied under ``models/v2/``):

- **Weapon**: YOLOv8 *detect* — ``weapon_detect_robust_v1``
- **Violence**: YOLOv8 *detect* — ``The_Witness/violence_model2``
- **Theft / robbery**: YOLOv8 *classify* — ``RobberyCls/robbery_v2_ft2`` (stored as ``THEFT`` in Django)

Used by the upload pipeline for annotated evidence frames, DB incidents, and FCM to SECURITY users.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

_weapon_model: Any = None
_violence_model: Any = None
_robbery_cls_model: Any = None
_lock = threading.Lock()
_load_error: Optional[str] = None


def _path_or_none(name: str) -> Optional[Path]:
    p = getattr(settings, name, None)
    if not p:
        return None
    path = Path(str(p))
    return path if path.is_file() else None


def _load_yolo(path: Path):
    from ultralytics import YOLO

    return YOLO(str(path))


def ensure_models():
    """Load v2 weights once per process. Returns (ok, error_message)."""
    global _weapon_model, _violence_model, _robbery_cls_model, _load_error
    if _load_error:
        return False, _load_error
    if _weapon_model is not None and _violence_model is not None and _robbery_cls_model is not None:
        return True, None
    with _lock:
        if _load_error:
            return False, _load_error
        if _weapon_model is not None:
            return True, None
        wp = _path_or_none("GODEYE_V2_WEAPON_WEIGHTS")
        vp = _path_or_none("GODEYE_V2_VIOLENCE_WEIGHTS")
        rp = _path_or_none("GODEYE_V2_ROBBERY_CLS_WEIGHTS")
        if not wp or not vp or not rp:
            _load_error = "Missing v2 weight files under models/v2/ (see GODEYE_V2_* in settings)."
            logger.error(_load_error)
            return False, _load_error
        try:
            _weapon_model = _load_yolo(wp)
            _violence_model = _load_yolo(vp)
            _robbery_cls_model = _load_yolo(rp)
        except Exception as e:
            _load_error = str(e)
            logger.exception("Failed to load GodsEye v2 models: %s", e)
            return False, _load_error
        return True, None


def v2_models_ready() -> bool:
    ok, _ = ensure_models()
    return ok


def _detection_boxes_and_top(
    model,
    frame_bgr: np.ndarray,
    imgsz: int,
    conf: float,
    label_match: Optional[list[str]],
) -> tuple[list[dict], float]:
    """Detection boxes; if ``label_match`` is set, keep boxes whose class name contains any token."""
    preds = model.predict(source=frame_bgr, imgsz=imgsz, conf=conf, verbose=False)
    if not preds:
        return [], 0.0
    r = preds[0]
    boxes = getattr(r, "boxes", None)
    if not boxes or len(boxes) == 0:
        return [], 0.0
    names = getattr(r, "names", None) or {}
    tokens: Optional[list[str]] = None
    if label_match:
        tokens = [t.lower() for t in label_match if t]

    def _iter_boxes():
        for b in boxes:
            try:
                c = float(b.conf.cpu().numpy()[0]) if hasattr(b.conf, "cpu") else float(b.conf[0])
            except Exception:
                try:
                    c = float(b.conf[0])
                except Exception:
                    c = 0.0
            try:
                cls = int(b.cls.cpu().numpy()[0]) if hasattr(b.cls, "cpu") else int(b.cls[0])
            except Exception:
                try:
                    cls = int(b.cls[0])
                except Exception:
                    cls = 0
            try:
                xyxy = b.xyxy.cpu().numpy()[0].tolist() if hasattr(b.xyxy, "cpu") else [float(x) for x in b.xyxy[0]]
            except Exception:
                xyxy = None
            yield cls, c, xyxy

    out: list[dict] = []
    top = 0.0
    for cls, c, xyxy in _iter_boxes():
        label_l = str(names.get(cls, cls)).lower()
        if tokens and not any(tok in label_l for tok in tokens):
            continue
        out.append({"xyxy": xyxy, "conf": c, "label": str(names.get(cls, cls))})
        top = max(top, c)

    # Single-class or odd class names: if filter removed everything, use all boxes
    if tokens and not out:
        out, top = [], 0.0
        for cls, c, xyxy in _iter_boxes():
            out.append({"xyxy": xyxy, "conf": c, "label": str(names.get(cls, cls))})
            top = max(top, c)

    return out, top


def _prob_for_class_name(model, frame_bgr: np.ndarray, imgsz: int, wanted: str) -> float:
    wanted_l = wanted.lower()
    preds = model.predict(source=frame_bgr, imgsz=imgsz, verbose=False)
    if not preds:
        return 0.0
    r = preds[0]
    names = getattr(r, "names", None) or {}
    idx = None
    for k, v in names.items():
        if str(v).lower() == wanted_l:
            idx = int(k)
            break
    if idx is None:
        return 0.0
    try:
        return float(r.probs.data[idx])
    except Exception:
        return 0.0


def weapon_on_frame(frame_bgr: np.ndarray) -> tuple[list[dict], float]:
    ok, _ = ensure_models()
    if not ok:
        return [], 0.0
    w_imgsz = int(getattr(settings, "GODEYE_V2_WEAPON_IMGSZ", 640))
    w_conf = float(getattr(settings, "GODEYE_V2_WEAPON_CONF", 0.25))
    return _detection_boxes_and_top(_weapon_model, frame_bgr, w_imgsz, w_conf, label_match=None)


def violence_on_frame(frame_bgr: np.ndarray) -> tuple[list[dict], float]:
    ok, _ = ensure_models()
    if not ok:
        return [], 0.0
    v_imgsz = int(getattr(settings, "GODEYE_V2_VIOLENCE_IMGSZ", 640))
    v_conf = float(getattr(settings, "GODEYE_V2_VIOLENCE_CONF", 0.25))
    match = list(getattr(settings, "GODEYE_V2_VIOLENCE_LABEL_MATCH", []))
    return _detection_boxes_and_top(_violence_model, frame_bgr, v_imgsz, v_conf, label_match=match or None)


def robbery_on_frame(frame_bgr: np.ndarray) -> float:
    ok, _ = ensure_models()
    if not ok:
        return 0.0
    cls_imgsz = int(getattr(settings, "GODEYE_V2_CLS_IMGSZ", 224))
    r_target = str(getattr(settings, "GODEYE_V2_ROBBERY_CLASS_NAME", "robbery"))
    return float(_prob_for_class_name(_robbery_cls_model, frame_bgr, cls_imgsz, r_target))


def build_annotated_frame(
    frame_bgr: np.ndarray,
    weapon_boxes: list[dict],
    violence_boxes: list[dict],
    robbery_p: float,
) -> np.ndarray:
    """BGR image with boxes and scores for security review (objective: annotated evidence)."""
    img = frame_bgr.copy()
    h, w = img.shape[:2]

    def _draw_boxes(boxes: list[dict], color: tuple[int, int, int]) -> None:
        for b in boxes:
            xyxy = b.get("xyxy")
            if not xyxy or len(xyxy) < 4:
                continue
            x1, y1, x2, y2 = [int(round(float(v))) for v in xyxy[:4]]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cap = f"{b.get('label', '')} {float(b.get('conf', 0)):.2f}"
            cv2.putText(img, cap, (x1, max(0, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    _draw_boxes(violence_boxes, (0, 165, 255))
    _draw_boxes(weapon_boxes, (0, 0, 255))
    cv2.putText(
        img,
        f"robbery_cls {robbery_p:.2f}",
        (10, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 128, 0),
        2,
        cv2.LINE_AA,
    )
    return img


def score_frame(frame_bgr: np.ndarray) -> dict:
    """Run all v2 models on one BGR frame (for tests / future live worker)."""
    ok, err = ensure_models()
    if not ok:
        return {"error": err}
    wb, wt = weapon_on_frame(frame_bgr)
    vb, vt = violence_on_frame(frame_bgr)
    rp = robbery_on_frame(frame_bgr)
    return {
        "weapon_boxes": wb,
        "weapon_top_conf": float(wt),
        "violence_boxes": vb,
        "violence_top_conf": float(vt),
        "violence_p": float(vt),
        "robbery_p": float(rp),
    }
