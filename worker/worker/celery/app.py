from celery import Celery

from worker.core.config import settings


celery_app = Celery(
    settings.CELERY_NAME,
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=settings.TIME_ZONE if settings.USE_TZ else None,
    enable_utc=True,
)
celery_app.autodiscover_tasks(['worker.celery'])
