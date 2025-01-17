from typing import Any

from app.core.config import settings
from .base import BaseAsyncAPIClient, authenticate
from .utils import APIClientException, retry


class BackendAPIClientException(APIClientException):
    pass


class OrchestratorAPIClient(BaseAsyncAPIClient):
    class OrchestratorAPIUrlSchema:
        ORCHESTRATOR_TASKS_URL = settings.ORCHESTRATOR_TASKS_API_URL
        UPDATE_APP_DATA = ORCHESTRATOR_TASKS_URL + 'update_app_data'
        BULK_UPDATE_APP_DATA = ORCHESTRATOR_TASKS_URL + 'bulk_update_app_data'
        UPDATE_APP_LIST = ORCHESTRATOR_TASKS_URL + 'update_app_list'
        GET_TASK_STATUS = ORCHESTRATOR_TASKS_URL

    @classmethod
    @retry()
    @authenticate
    async def register_update_app_data_task(
            cls, app_id: int, country_code: str, headers: dict[str, Any] | None = None) -> dict[str, Any]:

        async with cls.CLIENT() as client:
            response = await client.post(
                url=cls.OrchestratorAPIUrlSchema.UPDATE_APP_DATA,
                headers=headers,
                json={'app_id': app_id, 'country_code': country_code}
            )

            response.raise_for_status()

        return response.json()

    @classmethod
    @retry()
    @authenticate
    async def register_bulk_update_app_data_task(
            cls, app_ids: list[int], country_codes: list[str], headers: dict[str, Any] | None = None) -> dict[str, Any]:

        async with cls.CLIENT() as client:
            response = await client.post(
                url=cls.OrchestratorAPIUrlSchema.BULK_UPDATE_APP_DATA,
                headers=headers,
                json={'app_id': app_ids, 'country_code': country_codes}
            )

            response.raise_for_status()

        return response.json()

    @classmethod
    @retry()
    @authenticate
    async def register_update_app_list_task(cls, headers: dict[str, Any] | None = None):
        async with cls.CLIENT() as client:
            response = await client.post(
                url=cls.OrchestratorAPIUrlSchema.UPDATE_APP_LIST,
                headers=headers,
            )

            response.raise_for_status()

        return response.json()

    @classmethod
    @retry()
    @authenticate
    async def get_task_status(cls, task_id: str, headers: dict[str, Any] | None = None) -> dict[str, Any]:
        async with cls.CLIENT() as client:
            response = await client.get(
                url=cls.OrchestratorAPIUrlSchema.GET_TASK_STATUS + task_id,
                headers=headers,
            )

            response.raise_for_status()

        return response.json()
