from django.apps import AppConfig


class CamerasConfig(AppConfig):
    name = 'cameras'
    def ready(self):
        # import signals to ensure post_save behavior is registered
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
