import logging

from app.core.config import settings
from app.core.logger import get_logger
from app.utils.ftsearch_index.types import IndexBackend
from elasticsearch import AsyncElasticsearch


class ElasticsearchIndexBackend(IndexBackend):

    logger: logging.Logger = get_logger(settings, 'ftsearch_index.elastic')

    def __init__(self, es: AsyncElasticsearch, index_name: str):
        self._es = es
        self._index = index_name

    async def fulltext_search(self, value: str, fields: list[str] | None = None) -> list[int]:
        query = {
            "query": {
                "multi_match": {
                    "query": value,
                    "fields": fields if fields else ["*"],
                }
            }
        }

        try:
            response = await self._es.search(index=self._index, body=query)
        except Exception as e:
            self.logger.error(f'Received errors when trying to search in index: {e}')
            return []

        if errors := response.get('errors'):
            self.logger.error(f'Received errors when trying to search in index: {errors}')
            return []

        return [int(hit["_id"]) for hit in response["hits"]["hits"]]
