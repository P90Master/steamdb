from fastapi import APIRouter, Depends, Path

from app.api.schemas import (
    TaskResponseSchema,
    UpdateAppDataTaskRequestSchema,
    BulkUpdateAppDataTaskRequestSchema,
    TaskStatusResponseSchema,
)
from app.auth import Permissions
from app.external_api import OrchestratorAPIClient


router = APIRouter(prefix='/tasks')


@router.post('/update_app_data', status_code=201)
async def update_app_data_task(
    request: UpdateAppDataTaskRequestSchema, _ = Depends(Permissions.can_register_tasks)
) -> TaskResponseSchema:
    orchestrator_response = await OrchestratorAPIClient.register_update_app_data_task(
        app_id=request.app_id, country_code=request.country_code
    )
    return TaskResponseSchema(task_id=orchestrator_response.get('task_id'))


@router.post('/bulk_update_app_data', status_code=201)
async def bulk_update_app_data_task(
    request: BulkUpdateAppDataTaskRequestSchema, _ = Depends(Permissions.can_register_tasks)
) -> TaskResponseSchema:
    orchestrator_response = await OrchestratorAPIClient.register_bulk_update_app_data_task(
        app_ids=request.app_ids, country_codes=request.country_codes
    )
    return TaskResponseSchema(task_id=orchestrator_response.get('task_id'))


@router.post('/update_app_list', status_code=201)
async def update_app_list_task(_ = Depends(Permissions.can_register_tasks)) -> TaskResponseSchema:
    orchestrator_response = await OrchestratorAPIClient.register_update_app_list_task()
    return TaskResponseSchema(task_id=orchestrator_response.get('task_id'))


@router.get('/{task_id}', status_code=200)
async def get_task_status(
    task_id: str = Path(..., regex=r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'),
    _ = Depends(Permissions.can_register_tasks)
) -> TaskStatusResponseSchema:
    orchestrator_response = await OrchestratorAPIClient.get_task_status(task_id=task_id)
    return TaskStatusResponseSchema(status=orchestrator_response.get('status'))
