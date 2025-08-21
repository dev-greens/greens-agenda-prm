try:
    from .celery import app as celery_app
except Exception:
    celery_app = None  # evita quebrar se Celery não estiver disponível
__all__ = ("celery_app",)
