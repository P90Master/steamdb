import abc
from typing import Dict, Any

import aiohttp
from enum import Enum

from .base import APIClientException, BaseAsyncAPIClient, BaseAsyncSessionClient, handle_response_exceptions, retry
from worker.config import settings

class BackendAPIClientException(APIClientException):
    pass


class BackendAPI(abc.ABC):
    class BackendAPIUrl(Enum):
        app_data_package = f'{settings.BACKEND_HOST}/api/{settings.BACKEND_API_VERSION}/games/package/'

    @classmethod
    @property
    def get_app_data_package_endpoint(cls):
        return cls.BackendAPIUrl.app_data_package.value

    @abc.abstractmethod
    def post_app_data_package(self, *args, **kwargs):
        pass


class AsyncBackendSessionClient(BaseAsyncSessionClient, BackendAPI):
    SESSION_CLASS = aiohttp.ClientSession

    @handle_response_exceptions(component=__name__, url=BackendAPI.get_app_data_package_endpoint, method="POST")
    @retry()
    async def post_app_data_package(self, app_data_package: Dict[str, Any]):
        async with self._session.post(self.get_app_data_package_endpoint, json=app_data_package) as response:
            response.raise_for_status()
            return await response.json()


class AsyncBackendAPIClient(BaseAsyncAPIClient, BackendAPI):
    SESSION_CLIENT = AsyncBackendSessionClient
    SESSION_CLIENT_FOR_SINGLE_REQUESTS = aiohttp.ClientSession
    API_CLIENT_EXCEPTION_CLASS = BackendAPIClientException

    @handle_response_exceptions(component=__name__, url=BackendAPI.get_app_data_package_endpoint, method="POST")
    @retry()
    async def post_app_data_package(self, app_data_package: Dict[str, Any]):
        async with self.SESSION_CLIENT_FOR_SINGLE_REQUESTS() as session:
            async with session.post(self.get_app_data_package_endpoint, json=app_data_package) as response:
                response.raise_for_status()
                return await response.json()
