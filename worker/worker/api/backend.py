import abc
from typing import Any
from enum import Enum

import aiohttp

from .base import APIClientException, BaseAsyncAPIClient, BaseAsyncSessionClient, handle_response_exceptions, retry
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
    SESSION_CLASS = aiohttp.ClientSession

    @handle_response_exceptions(component=__name__, url=BackendAPI.get_app_data_package_endpoint, method="POST")
    @retry()
    async def post_app_data_package(self, app_data_package: dict[str, Any]) -> dict[str, Any]:
        async with self._session.post(self.get_app_data_package_endpoint, json=app_data_package) as response:
            response.raise_for_status()
            return await response.json()


class AsyncBackendAPIClient(BaseAsyncAPIClient, BackendAPI):
    SESSION_CLIENT = AsyncBackendSessionClient
    SESSION_CLIENT_FOR_SINGLE_REQUESTS = aiohttp.ClientSession
    API_CLIENT_EXCEPTION_CLASS = BackendAPIClientException

    @handle_response_exceptions(component=__name__, url=BackendAPI.get_app_data_package_endpoint, method="POST")
    @retry()
    async def post_app_data_package(self, app_data_package: dict[str, Any]) -> dict[str, Any]:
        async with self.SESSION_CLIENT_FOR_SINGLE_REQUESTS() as session:
            async with session.post(self.get_app_data_package_endpoint, json=app_data_package) as response:
                response.raise_for_status()
                return await response.json()
