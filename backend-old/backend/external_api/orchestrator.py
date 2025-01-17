from typing import List, Dict

import requests
from django.conf import settings

from enum import Enum


class OrchestratorAPIClient:
    class OrchestratorAPIUrl(Enum):
        _orchestrator_tasks_api_prefix = f'{settings.ORCHESTRATOR_URL}/api/{settings.ORCHESTRATOR_API_VERSION}/tasks/'
        update_app_data = f'{_orchestrator_tasks_api_prefix}update_app_data/'
        bulk_update_app_data = f'{_orchestrator_tasks_api_prefix}bulk_update_app_data/'
        update_app_list = f'{_orchestrator_tasks_api_prefix}update_app_list/'
        get_task_status = _orchestrator_tasks_api_prefix

    @classmethod
    @property
    def get__update_app_data__endpoint(cls):
        return cls.OrchestratorAPIUrl.update_app_data.value

    @classmethod
    @property
    def get__bulk_update_app_data__endpoint(cls):
        return cls.OrchestratorAPIUrl.bulk_update_app_data.value

    @classmethod
    @property
    def get__update_app_list__endpoint(cls):
        return cls.OrchestratorAPIUrl.update_app_list.value

    @classmethod
    @property
    def get__get_task_status__endpoint(cls):
        return cls.OrchestratorAPIUrl.get_task_status.value

    @staticmethod
    def _unpack_response(response: requests.Response) -> Dict[str, any]:
        return {
            'status': response.status_code,
            'data': response.json()
        }

    def register_update_app_data_task(self, app_id: int, country_code: str):
        data = {
            'app_id': app_id,
            'country_code': country_code
        }
        return self._unpack_response(
            requests.post(self.get__update_app_data__endpoint, json=data)
        )

    def register_bulk_update_app_data_task(self, app_ids: List[int], country_codes: List[str]):
        data = {
            'app_ids': app_ids,
            'country_codes': country_codes
        }
        return self._unpack_response(
            requests.post(self.get__bulk_update_app_data__endpoint, json=data)
        )

    def register_update_app_list_task(self):
        return self._unpack_response(
            requests.post(self.get__update_app_list__endpoint)
        )

    def get_task_status(self, task_id: str):
        url = f'{self.get__get_task_status__endpoint}{task_id}/'
        return self._unpack_response(
            requests.get(url)
        )
