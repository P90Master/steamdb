import abc
from typing import Any

import aiohttp
from enum import Enum

import requests

from worker.core.config import settings
from .base import (
    APIClientException,
    BaseAsyncAPIClient,
    BaseAsyncSessionClient,
    handle_response_exceptions,
)


class SteamAPIClientException(APIClientException):
    pass


class SteamAPI(abc.ABC):
    class SteamAPIUrl(Enum):
        app_list = settings.STEAM_APP_LIST_URL
        app_detail = settings.STEAM_APP_DETAIL_URL

    @classmethod
    @property
    def get_app_list_url(cls) -> str:
        return cls.SteamAPIUrl.app_list.value

    @classmethod
    @property
    def get_app_detail_url(cls) -> str:
        return cls.SteamAPIUrl.app_detail.value

    @abc.abstractmethod
    def get_app_list(self, *args, **kwargs) -> dict[str, Any]:
        ...

    @abc.abstractmethod
    def get_app_detail(self, *args, **kwargs) -> dict[str, Any]:
        ...


class SteamAPIClient(SteamAPI):
    def __init__(self, token: str | None = None):
        self._token: str | None = token

    @handle_response_exceptions(component=__name__, url=SteamAPI.get_app_list_url, method="GET")
    def get_app_list(self) -> dict[str, Any]:
        response = requests.get(self.get_app_list_url, params=None)
        response.raise_for_status()
        return response.json()

    @handle_response_exceptions(component=__name__, url=SteamAPI.get_app_detail_url, method="GET")
    def get_app_detail(self, app_id, country_code=settings.DEFAULT_COUNTRY_CODE) -> dict[str, Any]:
        params = {
            'appids': app_id,
            'cc': country_code,
        }

        response = requests.get(self.get_app_detail_url, params=params)
        response.raise_for_status()
        return response.json()


class AsyncSteamSessionClient(BaseAsyncSessionClient, SteamAPI):
    SESSION_CLASS = aiohttp.ClientSession

    @handle_response_exceptions(component=__name__, url=SteamAPI.get_app_list_url, method="GET")
    async def get_app_list(self) -> dict[str, Any]:
        async with self._session.get(self.get_app_list_url, params=None) as response:
            response.raise_for_status()
            return await response.json()

    @handle_response_exceptions(component=__name__, url=SteamAPI.get_app_detail_url, method="GET")
    async def get_app_detail(self, app_id: int, country_code: str = settings.DEFAULT_COUNTRY_CODE) -> dict[str, Any]:
        params = {
            'appids': app_id,
            'cc': country_code,
        }

        async with self._session.get(self.get_app_detail_url, params=params) as response:
            response.raise_for_status()
            return await response.json()


class AsyncSteamAPIClient(BaseAsyncAPIClient, SteamAPI):
    SESSION_CLIENT = AsyncSteamSessionClient
    SESSION_CLIENT_FOR_SINGLE_REQUESTS = aiohttp.ClientSession
    API_CLIENT_EXCEPTION_CLASS = SteamAPIClientException

    @handle_response_exceptions(component=__name__, url=SteamAPI.get_app_list_url, method="GET")
    async def get_app_list(self) -> dict[str, Any]:
        async with self.SESSION_CLIENT_FOR_SINGLE_REQUESTS() as session:
            async with session.get(self.get_app_list_url) as response:
                response.raise_for_status()
                return await response.json()

    @handle_response_exceptions(component=__name__, url=SteamAPI.get_app_detail_url, method="GET")
    async def get_app_detail(self, app_id: int, country_code: str =settings.DEFAULT_COUNTRY_CODE) -> dict[str, Any]:
        params = {
            'appids': app_id,
            'cc': country_code,
        }

        async with self.SESSION_CLIENT_FOR_SINGLE_REQUESTS() as session:
            async with session.get(self.get_app_detail_url, params=params) as response:
                response.raise_for_status()
                return await response.json()
