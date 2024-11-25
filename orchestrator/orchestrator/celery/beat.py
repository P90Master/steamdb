from celery import Celery
from celery.schedules import crontab

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

app.conf.beat_schedule = {
    'actualize_app_list': {
        'task': 'orchestrator.celery.tasks.scheduled.request_apps_list',
        'schedule': crontab(settings.CELERY_SCHEDULE_REQUEST_ACTUAL_APP_LIST),
    },
    'bulk_request_for_most_outdated_apps_data': {
        'task': 'orchestrator.celery.tasks.scheduled.bulk_request_for_most_outdated_apps_data',
        'schedule': crontab(settings.CELERY_SCHEDULE_REQUEST_FOR_APPS_DATA),
    }
}
