from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from redis.asyncio import ConnectionPool
from starlette_admin.contrib.sqla import Admin

from auth.models import (
    Client,
    Scope,
    AccessToken,
    RefreshToken,
    AdminToken,
    User,
    Role,
)
from auth.admin import (
    ClientView,
    UserView,
    ScopeView,
    RoleView,
    AccessTokenView,
    RefreshTokenView,
    AdminTokenView,
    AdminProvider,
)
from auth.db import engine
from auth.utils.cache import CacheManager, RedisBackend
from auth.core.config import settings
from auth.core.logger import get_logger


@asynccontextmanager
async def lifespan(app_: FastAPI):
    cache_pool = ConnectionPool.from_url(url=settings.CACHE_URL)
    redis_instance = redis.Redis(connection_pool=cache_pool)
    CacheManager.init(
        RedisBackend(redis_instance),
        prefix=settings.CACHE_PREFIX,
        expire=settings.CACHE_TIMEOUT,
        logger=get_logger(settings, 'cache'),
    )

    yield

    await cache_pool.disconnect()


app: FastAPI = FastAPI(
    title="Steam DB OAuth2.0 Server",
    version="0.0.1",
    license_info={
        "name": "MIT",
        "url": "https://github.com/P90Master/steamdb/blob/main/LICENSE",
    },
    lifespan=lifespan,
)

admin = Admin(
    engine=engine,
    auth_provider=AdminProvider(),
    statics_dir="/auth/static",
)
admin.add_view(UserView(User))
admin.add_view(ClientView(Client))
admin.add_view(RoleView(Role))
admin.add_view(ScopeView(Scope))
admin.add_view(AccessTokenView(AccessToken))
admin.add_view(RefreshTokenView(RefreshToken))
admin.add_view(AdminTokenView(AdminToken))
admin.mount_to(app)


from auth.api import api_router

app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "API root"}
