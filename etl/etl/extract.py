from etl.pipeline.types import AbstractQueue


def extract(output_queue: AbstractQueue):
    from redis import Redis

    from etl.core.config import settings
    from etl.state_storage import StateStorage, RedisStateStorageBackend
    from etl.pipeline.components import Extractor
    from etl.db import connect_to_db


    redis = Redis.from_url(settings.STATE_STORAGE_URL)
    db = connect_to_db(
        url=settings.MONGO_URL,
        db_name=settings.MONGO_DB,
        collection_name=settings.MONGO_COLLECTION
    )
    state_storage_backend = RedisStateStorageBackend(redis)
    state_storage = StateStorage(state_storage_backend, service_name="extractor")
    extractor = Extractor(db, state_storage=state_storage, output_queue=output_queue)
    extractor()


def transform(input_queue: AbstractQueue, output_queue: AbstractQueue):
    from redis import Redis

    from etl.core.config import settings
    from etl.state_storage import StateStorage, RedisStateStorageBackend
    from etl.pipeline.components import Transformer

    redis = Redis.from_url(settings.STATE_STORAGE_URL)
    state_storage_backend = RedisStateStorageBackend(redis)
    state_storage = StateStorage(state_storage_backend, service_name="transformer")
    transformer = Transformer(state_storage=state_storage, input_queue=input_queue, output_queue=output_queue)
    transformer()


def main():
    from multiprocessing import Process
    from redis import Redis

    from etl.core.config import settings
    from etl.pipeline.queues import InMemoryQueue, RedisQueue


    redis = Redis.from_url(settings.STATE_STORAGE_URL)
    transform_queue = InMemoryQueue()
    # TODO: separate state storage and queue
    load_queue = RedisQueue(redis, service_name="loader")

    extracting = Process(target=extract, args=(transform_queue,))
    transforming = Process(target=transform, args=(transform_queue, load_queue))
    extracting.start()
    transforming.start()
    extracting.join()
    transforming.join()


if __name__ == "__main__":
    main()
