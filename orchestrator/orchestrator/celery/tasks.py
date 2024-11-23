from orchestrator.messenger.tasks import TaskManager
from orchestrator.messenger.connections import worker_channel
from orchestrator.logger import get_logger
from orchestrator.config import settings
from orchestrator.db import Session
from .worker import app


logger = get_logger(settings, name='scheduled_task')
task_manager = TaskManager(messenger_channel=worker_channel, session_maker=Session, logger=logger)


@app.task
def request_apps_list(*args, **kwargs):
    task_manager.request_apps_list()


@app.task
def bulk_request_for_apps_data(*args, **kwargs):
    task_manager.bulk_request_for_apps_data()
