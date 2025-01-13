from etl.state_storage.types import StateStorageBackend
from redis import Redis
from typing import Optional


class RedisStateStorageBackend(StateStorageBackend):
    def __init__(self, redis: Redis):
        self._redis = redis

    def get(self, key: str) -> Optional[str]:
        return self._redis.get(key)

    def set(self, key: str, value: str):
        self._redis.set(key, value)
