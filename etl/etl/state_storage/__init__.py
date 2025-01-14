from datetime import datetime

from etl.utils import backoff
from orchestrator.celery.tasks.scheduled import priority
from .types import StateStorageBackend
from .backend import RedisStateStorageBackend
from etl.core.logger import get_logger
from etl.core.config import settings


class StateStorage:

    logger = get_logger(settings, 'state_storage')

    def __init__(
            self,
            backend_: StateStorageBackend,
            status_key: str = "status",
            service_name: str = "",
            last_loaded_key: str = "last_loaded"
    ):
        self._backend = backend_
        self._status_key = (f'{service_name}:' if service_name else '') + status_key
        self._last_loaded_key = last_loaded_key

    @property
    def is_running(self) -> bool:
        return self.get_status() == 'running'

    def set_running_status(self):
        self.set_status('running')

    def set_stopped_status(self):
        self.set_status('stopped')

    @backoff(start_sleep_time=5, max_sleep_time=60.0, factor=2.0, jitter=False, logger=logger)
    def get_status(self) -> str:
        return self._backend.get(self._status_key)

    @backoff(start_sleep_time=5, max_sleep_time=60.0, factor=2.0, jitter=False, logger=logger)
    def set_status(self, status: str):
        self._backend.set(self._status_key, status)

    @backoff(start_sleep_time=5, max_sleep_time=60.0, factor=2.0, jitter=False, logger=logger)
    def get_last_loaded(self) -> datetime:
        if datetime_ := self._backend.get(self._last_loaded_key):
            return datetime.fromisoformat(datetime_)

        return datetime.fromtimestamp(0)

    @backoff(start_sleep_time=5, max_sleep_time=60.0, factor=2.0, jitter=False, logger=logger)
    def set_last_loaded(self, datetime_: datetime):
        self._backend.set(self._last_loaded_key, str(datetime_))
