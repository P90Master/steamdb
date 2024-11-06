import asyncio

from worker.logger import logger

# FIXME rename current package to avoid collision with 3rd party?
from celery.exceptions import SoftTimeLimitExceeded


async def execute_celery_task(celery_task, *task_args, **task_kwargs):
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


async def wait_celery_task_result(celery_task):
    while not celery_task.ready():
        await asyncio.sleep(1)

    return celery_task.result
