from orchestrator.messenger.tasks import TaskManager
from orchestrator.messenger.connections import worker_channel
from orchestrator.logger import get_logger
from orchestrator.config import settings
from orchestrator.db import Session
from orchestrator.celery.worker import app


logger = get_logger(settings, name='scheduled_task')
task_manager = TaskManager(messenger_channel=worker_channel, session_maker=Session, logger=logger)


@app.task(time_limit=settings.CELERY_TASK_TIME_LIMIT)
def request_apps_list():
    task_manager.request_apps_list()


@app.task(time_limit=settings.CELERY_TASK_TIME_LIMIT)
def request_app_data(app_id: str, country_code: str):
    task_manager.request_app_data(app_id, country_code)


@app.task(time_limit=settings.CELERY_TASK_TIME_LIMIT)
def bulk_request_apps_data(app_ids: list[str], country_codes: list[str]):
    task_manager.bulk_request_for_apps_data(app_ids, country_codes)


@app.task(time_limit=settings.CELERY_TASK_TIME_LIMIT)
def bulk_request_for_most_outdated_apps_data(*args, **kwargs):
    task_manager.bulk_request_for_most_outdated_apps_data(*args, **kwargs)
