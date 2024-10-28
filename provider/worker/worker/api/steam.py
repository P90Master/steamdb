import abc
import aiohttp
from enum import Enum

# TODO change to root abs path
from worker.settings import DEFAULT_COUNTRY_CODE
from .base import APIClientException, BaseAPIClient, BaseSessionClient


class SteamAPIClientException(APIClientException):
    pass


class SteamAPI(abc.ABC):
    class SteamAPIUrl(Enum):
        # TODO Extracting from Settings (Pydantic)
        app_list = 'http://api.steampowered.com/ISteamApps/GetAppList/v2'
        app_detail = 'http://store.steampowered.com/api/appdetails'

    @property
    def get_app_list_url(self):
        return self.SteamAPIUrl.app_list.value

    @property
    def get_app_detail_url(self):
        return self.SteamAPIUrl.app_detail.value

    @abc.abstractmethod
    def get_app_list(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def get_app_detail(self, *args, **kwargs):
        pass


class SteamSessionClient(BaseSessionClient, SteamAPI):
    SESSION_CLASS = aiohttp.ClientSession

    async def get_app_list(self):
        try:
            async with self._session.get(self.get_app_list_url, params=None) as response:
                response.raise_for_status()
                return await response.json()

        except Exception as error:
            # TODO Log point here?
            raise error

    async def get_app_detail(self, app_id, country_code=DEFAULT_COUNTRY_CODE):
        params = {
            'appids': app_id,
            'cc': country_code,
        }

        try:
            async with self._session.get(self.get_app_detail_url, params=params) as response:
                response.raise_for_status()
                return await response.json()

        except Exception as error:
            # TODO Log point here?
            raise error


class SteamAPIClient(BaseAPIClient, SteamAPI):
    SESSION_CLIENT = SteamSessionClient
    SESSION_CLIENT_FOR_SINGLE_REQUESTS = aiohttp.ClientSession
    API_CLIENT_EXCEPTION_CLASS = SteamAPIClientException

    async def get_app_list(self):
        try:
            async with self.SESSION_CLIENT_FOR_SINGLE_REQUESTS() as session:
                async with session.get(self.get_app_list_url) as response:
                    response.raise_for_status()
                    return await response.json()

        except Exception as error:
            # TODO Log point here?
            raise error

    async def get_app_detail(self, app_id, country_code=DEFAULT_COUNTRY_CODE):
        params = {
            'appids': app_id,
            'cc': country_code,
        }

        try:
            async with self.SESSION_CLIENT_FOR_SINGLE_REQUESTS() as session:
                async with session.get(self.get_app_detail_url, params=params) as response:
                    response.raise_for_status()
                    return await response.json()

        except Exception as error:
            # TODO Log point here?
            raise error
