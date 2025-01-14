import logging
from typing import Any, ClassVar

from pymongo.collection import Collection

from etl.utils import coroutine, backoff, random_sleep
from etl.core.logger import get_logger
from etl.core.config import settings
from etl.models.db import App, AppInCountry, AppPrice
from etl.pipeline.types import PipelineComponent


class Extractor(PipelineComponent):

    logger: ClassVar[logging.Logger] = get_logger(settings, 'pipeline.extractor')

    def __init__(self, db: Collection, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db

    @backoff(start_sleep_time=5.0, max_sleep_time=60.0, logger=logger)
    def extract_from_db(self, serializer: callable):
        last_loaded = self.state_storage.get_last_loaded()

        while self.state_storage.is_running:
            self.logger.debug(f'Extracting apps from DB since {last_loaded}')

            apps = list(
                self.db.find({'updated_at': {'$gte': last_loaded}}).sort('updated_at', 1).limit(10)
            )
            if not apps:
                self.logger.debug('No new apps found in DB')
                random_sleep()
                continue

            self.logger.debug(f'Successfully extracted {len(apps)} apps from DB')
            last_loaded = apps[-1].get('updated_at', last_loaded)
            serializer.send(apps)

    @coroutine
    def serialize(self, pusher: callable):
        while True:
            apps: list[dict[str, Any]] = (yield)

            for app in apps:
                pusher.send(self.serialize_app_from_dump(app))


    @staticmethod
    def serialize_app_from_dump(app_dump: dict[str, Any]) -> App:
        app_in_countries: dict[str, AppInCountry] = {}

        for country, app_in_country in app_dump.get('prices', {}).items():
            app_prices: list[AppPrice] = [
                AppPrice(**app_price) for app_price in app_in_country.get('price_story', [])
            ]
            app_in_countries[country] = AppInCountry(
                is_available=app_in_country.get('is_available'),
                currency=app_in_country.get('currency'),
                price_story=app_prices
            )

        return App(
            id=app_dump.get('id'),
            name=app_dump.get('name'),
            type=app_dump.get('type'),
            short_description=app_dump.get('short_description'),
            is_free=app_dump.get('is_free'),
            developers=app_dump.get('developers'),
            publishers=app_dump.get('publishers'),
            total_recommendations=app_dump.get('total_recommendations'),
            prices=app_in_countries
        )

    @coroutine
    def push(self):
        while True:
            app: App = (yield)
            self.output_queue.put(app)

    def start(self):
        super().start()
        pusher = self.push()
        serializer = self.serialize(pusher)
        self.extract_from_db(serializer)
