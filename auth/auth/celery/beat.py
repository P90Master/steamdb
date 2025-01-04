from celery import Celery
from celery.schedules import crontab

from auth.core.config import settings

app = Celery(
    settings.CELERY_NAME,
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BROKER_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=settings.TIME_ZONE if settings.USE_TZ else None,
    enable_utc=True,
    worker_hijack_root_logger=False,
)

app.conf.beat_schedule = {
    'clean_expired_tokens': {
        'task': 'auth.celery.tasks.clean_expired_tokens',
        'schedule': crontab(*settings.CELERY_SCHEDULE_CLEAN_EXPIRED_TOKENS.split()),
    }
}
