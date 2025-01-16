import logging
from typing import Any, ClassVar

from elasticsearch import Elasticsearch

from etl.index import IndexBackend
from etl.utils import backoff
from etl.core.config import settings
from etl.core.logger import get_logger


class ElasticsearchIndexBackend(IndexBackend):

    logger: ClassVar[logging.Logger] = get_logger(settings, 'elastic')

    def __init__(self, es: Elasticsearch, index_name: str):
        self._es: Elasticsearch = es
        self._index: str = index_name

    @backoff(start_sleep_time=5.0, max_sleep_time=60.0, logger=logger)
    def ensure_index(self, index_body: dict[str, Any] | None = None):
        if not self._es.indices.exists(index=self._index):
            self._es.indices.create(index=self._index, body=index_body)

    def bulk_update(self, apps: list[dict[str, Any]]):
        if not apps:
            return

        actions: list[dict[str, Any]] = []
        for app in apps:
            actions.append(
                {
                    "index": {
                        "_index": self._index,
                        "_id": app['id'],
                    }
                }
            )
            actions.append(app)

        response = self._es.bulk(body=actions)
        if errors := response.get('errors'):
            raise IndexError(f'Received errors when trying to bulk update index: {errors}')
