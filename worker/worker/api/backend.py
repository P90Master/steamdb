import abc
from typing import Any
from enum import Enum

from .base import (
    APIClientException,
    BaseAsyncAPIClient,
    BaseAsyncSessionClient,
    handle_response_exceptions,
    retry,
    authenticate,
    authenticate_session
)
from worker.core.config import settings


class BackendAPIClientException(APIClientException):
    pass


class BackendAPI(abc.ABC):
    class BackendAPIUrl(Enum):
        app_data_package = settings.BACKEND_PACKAGE_ENDPOINT_URL

    @classmethod
    @property
    def get_app_data_package_endpoint(cls) -> str:
        return cls.BackendAPIUrl.app_data_package.value

    @abc.abstractmethod
    def post_app_data_package(self, app_data_package: dict[str, Any]) -> dict[str, Any]:
        ...


class AsyncBackendSessionClient(BaseAsyncSessionClient, BackendAPI):
    """
    async with AsyncBackendAPIClient() as backend_session:
        await backend_session.post_app_data_package(app_data_package)
    """

    @handle_response_exceptions(component=__name__, url=BackendAPI.get_app_data_package_endpoint, method="POST")
    @retry()
    @authenticate_session
    async def post_app_data_package(
            self,
            app_data_package: dict[str, Any],
            headers: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        async with self._session.post(self.get_app_data_package_endpoint, json=app_data_package, headers=headers) as response:
            response.raise_for_status()
            return await response.json()


class AsyncBackendAPIClient(BaseAsyncAPIClient, BackendAPI):
    SESSION_CLIENT = AsyncBackendSessionClient
    API_CLIENT_EXCEPTION_CLASS = BackendAPIClientException

    @handle_response_exceptions(component=__name__, url=BackendAPI.get_app_data_package_endpoint, method="POST")
    @retry()
    @authenticate
    async def post_app_data_package(
            self,
            app_data_package: dict[str, Any],
            headers: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        async with self.CLIENT_FOR_SINGLE_REQUESTS() as session:
            async with session.post(self.get_app_data_package_endpoint, json=app_data_package, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
