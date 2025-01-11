from fastapi import APIRouter, Depends, Path

from app.api.schemas import (
    TaskResponseSchema,
    UpdateAppDataTaskRequestSchema,
    BulkUpdateAppDataTaskRequestSchema,
    TaskStatusResponseSchema,
)
from app.auth import Permissions


router = APIRouter(prefix='/tasks')


@router.post('/update_app_data', status_code=201)
async def update_app_data_task(
    request: UpdateAppDataTaskRequestSchema, _ = Depends(Permissions.can_register_tasks)
) -> TaskResponseSchema:
    ...


@router.post('/update_app_data', status_code=201)
async def bulk_update_app_data_task(
    request: BulkUpdateAppDataTaskRequestSchema, _ = Depends(Permissions.can_register_tasks)
) -> TaskResponseSchema:
    ...


@router.post('/update_app_list', status_code=201)
async def update_app_list_task(_ = Depends(Permissions.can_register_tasks)) -> TaskResponseSchema:
    ...


@router.get('/{task_id}', status_code=200)
async def get_task_status(
    task_id: str = Path(..., regex=r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'),
    _ = Depends(Permissions.can_register_tasks)
) -> TaskStatusResponseSchema:
    ...
