"""
Firebase Cloud Messaging (FCM) for alerting stakeholders on the companion mobile app.

Set FCM_CREDENTIALS_PATH in settings to your Firebase service account JSON file,
or set GOOGLE_APPLICATION_CREDENTIALS in the environment (firebase_admin picks it up).
"""
from __future__ import annotations

import logging
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

_app_initialized = False


def _ensure_firebase_app() -> bool:
    global _app_initialized
    if _app_initialized:
        return True
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError:
        logger.warning("firebase_admin is not installed; push notifications are disabled.")
        return False

    cred_path = getattr(settings, "FCM_CREDENTIALS_PATH", None)
    if cred_path:
        p = Path(cred_path)
        if not p.is_file():
            logger.warning("FCM_CREDENTIALS_PATH does not point to a file: %s", cred_path)
            return False
        try:
            firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(str(p))
            firebase_admin.initialize_app(cred)
        _app_initialized = True
        return True

    # Let Application Default Credentials / GOOGLE_APPLICATION_CREDENTIALS work
    try:
        import firebase_admin
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app()
        _app_initialized = True
        return True
    except Exception as e:
        logger.warning("Firebase could not be initialized: %s", e)
        return False


def send_incident_push(alert) -> str:
    """
    Send a push for an Alert instance. Updates alert.delivery_status and saves.

    Returns the new delivery_status ('DELIVERED' or 'FAILED').
    """
    user = alert.user
    token = (getattr(user, "fcm_device_token", None) or "").strip()
    if not token:
        alert.delivery_status = "FAILED"
        alert.save(update_fields=["delivery_status"])
        return alert.delivery_status

    if not _ensure_firebase_app():
        alert.delivery_status = "FAILED"
        alert.save(update_fields=["delivery_status"])
        return alert.delivery_status

    from firebase_admin import messaging

    incident = alert.incident
    title = "The Witness — incident alert"
    body = f"{incident.get_incident_type_display()} detected (confidence {incident.confidence:.2f})"

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data={
            "type": "incident_alert",
            "alert_id": str(alert.id),
            "incident_id": str(incident.id),
            "incident_type": str(incident.incident_type),
        },
        token=token,
    )

    try:
        messaging.send(message)
        alert.delivery_status = "DELIVERED"
    except Exception as e:
        logger.exception("FCM send failed: %s", e)
        alert.delivery_status = "FAILED"

    alert.save(update_fields=["delivery_status"])
    return alert.delivery_status
