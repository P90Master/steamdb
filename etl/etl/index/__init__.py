import logging
from typing import ClassVar

from etl.core.logger import get_logger
from etl.core.config import settings
from etl.index.types import IndexBackend
from etl.utils import backoff
from etl.models import IndexedApp


class Index:

    logger: ClassVar[logging.Logger] = get_logger(settings, 'index')

    def __init__(self, backend: IndexBackend):
        self._backend: IndexBackend = backend

    @backoff(start_sleep_time=5, max_sleep_time=60.0, logger=logger)
    def bulk_update(self, apps: list[IndexedApp]):
        if not apps:
            return

        self._backend.bulk_update([app.__dict__ for app in apps])
