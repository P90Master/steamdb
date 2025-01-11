from typing import Any

from app.core.config import settings
from .base import BaseAsyncAPIClient, authenticate
from .utils import APIClientException, handle_response_exceptions, retry


class BackendAPIClientException(APIClientException):
    pass


class OrchestratorAPIClient(BaseAsyncAPIClient):
    class OrchestratorAPIUrlSchema:
        UPDATE_APP_DATA = settings.ORCHESTRATOR_TASKS_API_URL + 'update_app_data'
        BULK_UPDATE_APP_DATA = settings.ORCHESTRATOR_TASKS_API_URL + 'bulk_update_app_data'
        UPDATE_APP_LIST = settings.ORCHESTRATOR_TASKS_API_URL + 'update_app_list'
        GET_TASK_STATUS = settings.ORCHESTRATOR_TASKS_API_URL

    @handle_response_exceptions(component=__name__, url=OrchestratorAPIUrlSchema.UPDATE_APP_DATA, method="POST")
    @retry()
    @authenticate
    @classmethod
    async def register_update_app_data_task(
            cls, app_id: int, country_code: str, headers: dict[str, Any] | None = None) -> dict[str, Any]:

        with cls.CLIENT() as client:
            response = await client.post(
                url=cls.OrchestratorAPIUrlSchema.UPDATE_APP_DATA,
                headers=headers,
                json={'app_id': app_id, 'country_code': country_code}
            )

            response.raise_for_status()

        return response.json()

    @handle_response_exceptions(component=__name__, url=OrchestratorAPIUrlSchema.BULK_UPDATE_APP_DATA, method="POST")
    @retry()
    @authenticate
    @classmethod
    async def register_bulk_update_app_data_task(
            cls, app_ids: list[int], country_codes: list[str], headers: dict[str, Any] | None = None) -> dict[str, Any]:

        with cls.CLIENT() as client:
            response = await client.post(
                url=cls.OrchestratorAPIUrlSchema.BULK_UPDATE_APP_DATA,
                headers=headers,
                json={'app_id': app_ids, 'country_code': country_codes}
            )

            response.raise_for_status()

        return response.json()

    @handle_response_exceptions(component=__name__, url=OrchestratorAPIUrlSchema.UPDATE_APP_LIST, method="POST")
    @retry()
    @authenticate
    @classmethod
    async def register_update_app_list_task(cls, headers: dict[str, Any] | None = None):
        with cls.CLIENT() as client:
            response = await client.post(
                url=cls.OrchestratorAPIUrlSchema.UPDATE_APP_LIST,
                headers=headers,
            )

            response.raise_for_status()

        return response.json()

    @handle_response_exceptions(component=__name__, url=OrchestratorAPIUrlSchema.GET_TASK_STATUS, method="GET")
    @retry()
    @authenticate
    @classmethod
    async def get_task_status(cls, task_id: str, headers: dict[str, Any] | None = None) -> dict[str, Any]:
        with cls.CLIENT() as client:
            response = await client.get(
                url=cls.OrchestratorAPIUrlSchema.UPDATE_APP_LIST + task_id,
                headers=headers,
            )

            response.raise_for_status()

        return response.json()
