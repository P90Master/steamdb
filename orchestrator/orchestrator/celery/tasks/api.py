from orchestrator.messenger.tasks import TaskManager
from orchestrator.messenger.connections import create_channel
from orchestrator.logger import get_logger
from orchestrator.config import settings
from orchestrator.db import Session
from orchestrator.celery.worker import app


logger = get_logger(settings, name='messenger.received_api_task')
priority = settings.TASKS_FROM_API_PRIORITY


@app.task(time_limit=settings.CELERY_TASK_TIME_LIMIT)
def request_apps_list():
    worker_channel, worker_connection = create_channel()
    task_manager = TaskManager(
        messenger_channel=worker_channel,
        session_maker=Session,
        logger=logger,
        send_msg_with_priority=priority,
    )
    task_manager.request_apps_list()
    worker_connection.close()


@app.task(time_limit=settings.CELERY_TASK_TIME_LIMIT)
def request_app_data(app_id: str, country_code: str):
    worker_channel, worker_connection = create_channel()
    task_manager = TaskManager(
        messenger_channel=worker_channel,
        session_maker=Session,
        logger=logger,
        send_msg_with_priority=priority,
    )
    task_manager.request_app_data(app_id, country_code)
    worker_connection.close()


@app.task(time_limit=settings.CELERY_TASK_TIME_LIMIT)
def bulk_request_apps_data(app_ids: list[str], country_codes: list[str]):
    worker_channel, worker_connection = create_channel()
    task_manager = TaskManager(
        messenger_channel=worker_channel,
        session_maker=Session,
        logger=logger,
        send_msg_with_priority=priority,
    )
    task_manager.bulk_request_for_apps_data(app_ids, country_codes)
    worker_connection.close()


@app.task(time_limit=settings.CELERY_TASK_TIME_LIMIT)
def bulk_request_for_most_outdated_apps_data(*args, **kwargs):
    worker_channel, worker_connection = create_channel()
    task_manager = TaskManager(
        messenger_channel=worker_channel,
        session_maker=Session,
        logger=logger,
        send_msg_with_priority=priority,
    )
    task_manager.bulk_request_for_most_outdated_apps_data(*args, **kwargs)
    worker_connection.close()
