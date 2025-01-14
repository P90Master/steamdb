from elasticsearch import Elasticsearch
from redis import Redis

from etl.core.config import settings
from etl.utils import load_json
from etl.index import Index
from etl.index.backend import ElasticsearchIndexBackend
from etl.pipeline.components.loader import Loader
from etl.pipeline.queues import RedisQueue
from etl.state_storage import RedisStateStorageBackend, StateStorage


if __name__ == "__main__":
    redis_for_queue = Redis.from_url(settings.STATE_STORAGE_URL)
    load_queue = RedisQueue(redis_for_queue, service_name="loader")

    # TODO: separate state storage and queue
    redis_for_state = Redis.from_url(settings.STATE_STORAGE_URL)
    state_storage_backend = RedisStateStorageBackend(redis_for_state)
    state_storage = StateStorage(state_storage_backend, service_name="loader")

    es = Elasticsearch(
        [settings.ELASTICSEARCH_URL],
        basic_auth=(settings.ELASTICSEARCH_USER, settings.ELASTICSEARCH_PASSWORD)
    )
    index_backend = ElasticsearchIndexBackend(es, settings.ELASTICSEARCH_INDEX)
    es_index = load_json(settings.ELASTICSEARCH_INDEX_PATH)
    index_backend.ensure_index(es_index)
    index = Index(index_backend)

    loader = Loader(index=index, state_storage=state_storage, input_queue=load_queue)
    loader()
