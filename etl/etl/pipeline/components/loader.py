import logging
from typing import Any, ClassVar

from etl.index import Index
from etl.utils import coroutine, backoff
from etl.core.logger import get_logger
from etl.core.config import settings
from etl.models.db import App
from etl.models.index import IndexedApp
from etl.pipeline.types import PipelineComponent


class Loader(PipelineComponent):

    logger: ClassVar[logging.Logger] = get_logger(settings, 'pipeline.loader')

    def __init__(self, index: Index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index

    @backoff(start_sleep_time=5.0, max_sleep_time=60.0, logger=logger)
    def pull(self, loader: callable):
        while self.state_storage.is_running:
            apps: list[dict[str, Any]] = self.input_queue.get_batch(amount=10)
            loader.send(apps)

    @backoff(start_sleep_time=5.0, max_sleep_time=60.0, logger=logger)
    @coroutine
    def load(self):
        while True:
            apps: list[dict[str, Any]] = (yield)
            self.index.bulk_update(apps)
            self.logger.debug(f'Successfully loaded {len(apps)} apps')
            last_loaded = self.state_storage.get_last_loaded()
            self.state_storage.set_last_loaded(apps[-1].get('updated_at', last_loaded))

    def start(self):
        super().start()
        loader = self.load()
        self.pull(loader)
