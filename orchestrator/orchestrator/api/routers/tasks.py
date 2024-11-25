from fastapi import APIRouter

from orchestrator.celery.tasks.api import request_apps_list, request_app_data, bulk_request_apps_data
from orchestrator.celery import get_task_status

from orchestrator.api.schemas.tasks import TaskResponse, AppDataRequest, AppDataBulkRequest, TaskStatusResponse


router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.post("/update_app_data")
async def update_app_data(data: AppDataRequest) -> TaskResponse:
    task = request_app_data.delay(app_id=data.app_id, country_code=data.country_code)
    return TaskResponse(task_id=task.id)


@router.post("/bulk_update_app_data")
async def bulk_update_app_data(data: AppDataBulkRequest) -> TaskResponse:
    task = bulk_request_apps_data.delay(app_ids=data.app_ids, country_codes=data.country_codes)
    return TaskResponse(task_id=task.id)


@router.post("/update_app_list")
async def update_app_list() -> TaskResponse:
    task = request_apps_list.delay()
    return TaskResponse(task_id=task.id)


@router.get("/{task_id: str}")
async def task_status(task_id: str) -> TaskStatusResponse:
    status = get_task_status(task_id)
    return TaskStatusResponse(status=status)
