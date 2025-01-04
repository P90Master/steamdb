from celery import Celery

from auth.core.config import settings


app = Celery(
    settings.CELERY_NAME,
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=settings.TIME_ZONE if settings.USE_TZ else None,
    enable_utc=True,
    worker_hijack_root_logger=False,
)
app.autodiscover_tasks(['auth.celery.tasks'])
