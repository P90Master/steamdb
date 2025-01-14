from etl.state_storage.types import StateStorageBackend
from redis import Redis


class RedisStateStorageBackend(StateStorageBackend):
    def __init__(self, redis: Redis):
        self._redis = redis

    def get(self, key: str) -> str | None:
        return result.decode("utf-8") if (result := self._redis.get(key)) else None

    def set(self, key: str, value: str):
        self._redis.set(key, value)
