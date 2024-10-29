import abc
from typing import Dict, Any

import aiohttp
from enum import Enum

from .base import APIClientException, BaseAPIClient, BaseSessionClient

class BackendAPIClientException(APIClientException):
    pass


class BackendAPI(abc.ABC):
    class BackendAPIUrl(Enum):
        # TODO Extracting from Settings (Pydantic)
        app_data_package = 'http://127.0.0.1:8000/api/v1/games/package/'

    @property
    def get_app_data_package_endpoint(self):
        return self.BackendAPIUrl.app_data_package.value

    @abc.abstractmethod
    def post_app_data_package(self, *args, **kwargs):
        pass


class BackendSessionClient(BaseSessionClient, BackendAPI):
    SESSION_CLASS = aiohttp.ClientSession

    async def post_app_data_package(self, app_data_package: Dict[str, Any]):
        try:
            async with self._session.post(self.get_app_data_package_endpoint, json=app_data_package) as response:
                response.raise_for_status()
                return await response.json()

        except Exception as error:
            # TODO Log point here?
            raise error


class BackendAPIClient(BaseAPIClient, BackendAPI):
    SESSION_CLIENT = BackendSessionClient
    SESSION_CLIENT_FOR_SINGLE_REQUESTS = aiohttp.ClientSession
    API_CLIENT_EXCEPTION_CLASS = BackendAPIClientException

    async def post_app_data_package(self, app_data_package: Dict[str, Any]):
        try:
            async with self.SESSION_CLIENT_FOR_SINGLE_REQUESTS() as session:
                async with session.post(self.get_app_data_package_endpoint, json=app_data_package) as response:
                    response.raise_for_status()
                    return await response.json()

        except Exception as error:
            # TODO Log point here?
            raise error
