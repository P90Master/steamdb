from typing import Optional

from redis.asyncio.client import Redis

from app.utils.cache.types import Backend


class RedisBackend(Backend):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[bytes]:
        return await self.redis.get(key)

    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> None:
        await self.redis.set(key, value, ex=expire)

    async def clear(self, namespace: Optional[str] = None, key: Optional[str] = None) -> int:
        if namespace:
            lua = f"for i, name in ipairs(redis.call('KEYS', '{namespace}:*')) do redis.call('DEL', name); end"
            return await self.redis.eval(lua, numkeys=0)  # type: ignore[union-attr,no-any-return]

        if key:
            return await self.redis.delete(key)

        return 0
