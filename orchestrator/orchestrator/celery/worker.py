from celery import Celery

from orchestrator.config import settings


app = Celery(
    settings.CELERY_NAME,
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    worker_hijack_root_logger=False,
)
app.autodiscover_tasks(['orchestrator.celery.tasks.scheduled', 'orchestrator.celery.tasks.api'])
