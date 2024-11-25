from celery.result import AsyncResult


def get_task_status(task_id: str):
    task = AsyncResult(task_id)
    # TODO: if task with this id doesn't exist - it has PENDING status like running task
    return task.status
