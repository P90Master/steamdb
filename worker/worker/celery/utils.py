import asyncio
from typing import Any

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from celery.result import AsyncResult

from worker.core.config import settings
from worker.core.logger import get_logger



logger = get_logger(settings)


async def execute_celery_task(celery_task: Task, *task_args, **task_kwargs) -> tuple[Any, bool]:
    launched_celery_task = None

    try:
        launched_celery_task = celery_task.delay(*task_args, **task_kwargs)
        result = await wait_celery_task_result(launched_celery_task)
        return result, True

    except SoftTimeLimitExceeded:
        logger.error(
            f"Task {launched_celery_task if launched_celery_task else celery_task} wasn't completed on time."
        )
        return None, False

    except Exception as error:
        logger.error(
            f"An unexpected error was encountered while attempting to execute task."
            f" Task: {launched_celery_task if launched_celery_task else celery_task}"
            f" Error: {error}"
        )
        return None, False


async def wait_celery_task_result(celery_task: AsyncResult) -> Any:
    # Primitive hack for non-blocking waiting for task results in an asynchronous context
    # TODO: add timeout? (But await hasn't)

    while not celery_task.ready():
        await asyncio.sleep(0.1)

    return celery_task.result
