from orchestrator.messenger.tasks import TaskManager
from orchestrator.messenger.connections import create_channel
from orchestrator.core.logger import get_logger
from orchestrator.core.config import settings
from orchestrator.db import Session
from orchestrator.celery.worker import app


logger = get_logger(settings, name='messenger.scheduled_task')
priority = settings.SCHEDULED_TASKS_PRIORITY


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
