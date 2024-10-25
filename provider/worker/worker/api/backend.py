from typing import Dict, Any

import aiohttp
from enum import Enum


class SteamAPI:
    class BackendAPIUrl(Enum):
        # TODO Extracting from Settings (Pydantic)
        app_data_package = 'http://127.0.0.1:8000/api/v1/games/package/'

    def __init__(self, token):
        self._token = token
        # TODO use session_manager? (Auth)
        self._session = aiohttp.ClientSession()

    @property
    def get_app_data_package_endpoint(self):
        return self.BackendAPIUrl.app_data_package.value

    async def post_app_list(self, app_data: Dict[str, Any]):
        converted_app_data = self.convert_app_data(app_data)

        try:
            async with self._session.post(self.get_app_data_package_endpoint, params=None) as response:
                response.raise_for_status()
                return await response.json()

        except Exception as error:
            # TODO Log point here?
            raise error

    @staticmethod
    def convert_app_data(app_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
