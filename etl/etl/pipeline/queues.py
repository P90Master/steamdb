import time
from queue import Queue, Empty
from typing import Any

from redis import Redis

from etl.utils import backoff
from .types import AbstractQueue
from etl.core.config import settings
from etl.core.logger import get_logger


IN_MEMORY_QUEUE_MAX_SIZE = 100
REDIS_QUEUE_MAX_SIZE = 100


class InMemoryQueue(AbstractQueue):
    def __init__(self, max_size: int = IN_MEMORY_QUEUE_MAX_SIZE):
        self._queue = Queue(maxsize=max_size)

    def get(self) -> Any:
        return self._queue.get()

    def get_batch(self, amount: int = 1, wait_full: bool = False) -> list[Any]:
        if amount < 1:
            return []

        if wait_full:
            return [self._queue.get() for _ in range(amount)]

        batch = [self._queue.get()]

        try:
            for _ in range(amount - 1):
                batch.append(self._queue.get_nowait())
        except Empty:
            pass

        return batch


    def put(self, item: Any):
        self._queue.put(item)


class RedisQueue(AbstractQueue):

    logger = get_logger(settings, 'redis_queue')

    def __init__(self, redis: Redis, service_name: str, max_size: int = REDIS_QUEUE_MAX_SIZE):
        self._redis = redis
        self._max_size = max_size
        self._queue_name = f"{service_name}:queue"

    @backoff(start_sleep_time=5.0, max_sleep_time=60.0, logger=logger)
    def get(self) -> Any:
        keys_list = [self._queue_name]

        while True:
            result = self._redis.brpop(keys_list, timeout=5)
            if result:
                return result[1].decode("utf-8")

    @backoff(start_sleep_time=5.0, max_sleep_time=60.0, logger=logger)
    def get_batch(self, amount: int = 1, wait_full: bool = False) -> list[Any]:
        if amount < 1:
            return []

        keys_list = [self._queue_name]

        if wait_full:
            return [self.get() for _ in range(amount)]

        batch: list[Any] = [self.get()]

        result = self._redis.lmpop(1, keys_list, direction="RIGHT", count=amount - 1)
        if result:
            batch.extend(item.decode("utf-8") for item in result[1])

        return batch


    @backoff(start_sleep_time=5.0, max_sleep_time=60.0, logger=logger)
    def put(self, item: Any) -> None:
        while True:
            if self._redis.llen(self._queue_name) < self._max_size:
                self._redis.lpush(self._queue_name, item)
                break

            else:
                time.sleep(5)
