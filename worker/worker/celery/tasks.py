from worker.celery.app import celery_app
from worker.config import settings
from worker.connections import steam_api_client


@celery_app.task(
    name="get_app_list",
    rate_limit=settings.CELERY_TASK_COMMON_RATE_LIMIT,
    time_limit=settings.CELERY_TASK_TIME_LIMIT,
)
def get_app_list_celery_task(*args, **kwargs):
    return steam_api_client.get_app_list()


@celery_app.task(
    name="get_app_detail",
    rate_limit=settings.CELERY_TASK_COMMON_RATE_LIMIT,
    time_limit=settings.CELERY_TASK_TIME_LIMIT,
)
def get_app_detail_celery_task(*args, **kwargs):
    return steam_api_client.get_app_detail(*args, **kwargs)
