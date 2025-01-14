import logging
from typing import Any, ClassVar

from etl.utils import coroutine, backoff
from etl.core.logger import get_logger
from etl.core.config import settings
from etl.models.db import App
from etl.models.index import IndexedApp
from etl.pipeline.types import PipelineComponent


class Transformer(PipelineComponent):

    logger: ClassVar[logging.Logger] = get_logger(settings, 'pipeline.transformer')

    @backoff(start_sleep_time=5.0, max_sleep_time=60.0, logger=logger)
    def pull(self, transformer: callable):
        while self.state_storage.is_running:
            apps = self.input_queue.get_batch(amount=10)
            transformer.send(apps)

    @coroutine
    def transform(self, serializer: callable):
        while True:
            apps: list[App] = (yield)

            for app in apps:
                serializer.send(
                    IndexedApp(
                        id=app.id,
                        name=app.name,
                        updated_at=app.updated_at,
                        short_description=app.short_description,
                        developers=app.developers,
                        publishers=app.publishers,
                    )
                )

            self.logger.info(f'Successfully transformed {len(apps)} apps')

    @coroutine
    def serialize(self, pusher: callable):
        while True:
            app: IndexedApp = (yield)
            app_dump = app.__dict__
            app_dump['updated_at'] = app_dump['updated_at'].isoformat()
            pusher.send(app_dump)

    @coroutine
    def push(self):
        while True:
            app: dict[str, Any] = (yield)
            self.output_queue.put(app)

    def start(self):
        super().start()
        pusher = self.push()
        serializer = self.serialize(pusher)
        transformer = self.transform(serializer)
        self.pull(transformer)
