import aiohttp
from enum import Enum


class SteamAPI:
    class SteamAPIUrl(Enum):
        # TODO Extracting from Settings (Pydantic)
        app_list = 'http://api.steampowered.com/ISteamApps/GetAppList/v2'
        app_detail = 'http://store.steampowered.com/api/appdetails'

    def __init__(self, token):
        self._token = token
        self._session = aiohttp.ClientSession()

    @property
    def get_app_list_endpoint(self):
        return self.SteamAPIUrl.app_list.value

    @property
    def get_app_detail_endpoint(self):
        return self.SteamAPIUrl.app_detail.value

    async def get_app_list(self):
        try:
            async with self._session.get(self.get_app_list_endpoint, params=None) as response:
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
            async with self._session.get(self.get_app_detail_endpoint, params=params) as response:
                response.raise_for_status()
                return await response.json()

        except Exception as error:
            # TODO Log point here?
            raise error
