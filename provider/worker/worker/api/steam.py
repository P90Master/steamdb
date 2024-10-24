import aiohttp
import asyncio
from enum import Enum


class SessionManagerException(Exception):
    pass


class SessionManager:
    """
    Creates a session and ensures that it does not close prematurely.
    """

    def __init__(self, *session_args, **session_kwargs):
        self._readers = 0
        self._session = None
        self._lock = asyncio.Lock()
        self._session_args = session_args
        self._session_kwargs = session_kwargs

    async def __aenter__(self):
        async with self._lock:
            self._readers += 1

            if self._readers == 1:
                self._session = aiohttp.ClientSession(*self._session_args, **self._session_kwargs)
                return self._session

            if self._session is None:
                raise SessionManagerException('Session has readers, but has not been initialized')

            return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async with self._lock:
            self._readers -= 1

            if self._readers == 0:
                await self._session.close()
                self._session = None

            return False


class SteamAPI:
    class SteamAPIUrl(Enum):
        # TODO Extracting from Settings (Pydantic)
        app_list = 'http://api.steampowered.com/ISteamApps/GetAppList/v2'
        app_detail = 'http://store.steampowered.com/api/appdetails'

    def __init__(self, token):
        self._token = token
        self._session_manager = SessionManager()

    @property
    def get_app_list_endpoint(self):
        return self.SteamAPIUrl.app_list.value

    @property
    def get_app_detail_endpoint(self):
        return self.SteamAPIUrl.app_detail.value

    @staticmethod
    def _execute_get(session, url, params=None):
        pass

    async def get_app_list(self):
        try:
            async with self._session_manager as session:
                async with session.get(self.get_app_list_endpoint, params=None) as response:
                    response.raise_for_status()
                    return await response.json()

        except Exception as error:
            # TODO Log point here?
            raise error

    async def get_app_detail(self, app_id, country_code='US'):
        params = {
            'appid': app_id,
            'cc': country_code,
        }

        try:
            async with self._session_manager as session:
                async with session(self.get_app_detail_endpoint, params=params) as response:
                    response.raise_for_status()
                    return await response.json()

        except Exception as error:
            # TODO Log point here?
            raise error
