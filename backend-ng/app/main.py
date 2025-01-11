from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import ConnectionPool
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import get_logger
from app.utils.cache import CacheManager, RedisBackend
from app.models import DOCUMENTS
from app.middlewares import ReplaceQueryParamsMiddleware, AuthMiddleware, ExceptionHandlerMiddleware
from app.external_api import OrchestratorAPIClient


@asynccontextmanager
async def lifespan(app_: FastAPI):
    app_.db_client = getattr(AsyncIOMotorClient(settings.MONGO_URL), settings.MONGO_DB)
    await init_beanie(app_.db_client, document_models=DOCUMENTS)

    cache_pool = ConnectionPool.from_url(url=settings.CACHE_URL)
    redis_instance = redis.Redis(connection_pool=cache_pool)
    CacheManager.init(
        RedisBackend(redis_instance),
        prefix=settings.CACHE_PREFIX,
        expire=settings.CACHE_TIMEOUT,
        logger=get_logger(settings, 'cache'),
    )

    OrchestratorAPIClient.init(
        client_id=settings.ESSENTIAL_BACKEND_CLIENT_ID,
        client_secret=settings.ESSENTIAL_BACKEND_CLIENT_SECRET
    )

    yield

    OrchestratorAPIClient.reset()
    CacheManager.reset()
    app_.db_client.close()
    await cache_pool.disconnect()


app = FastAPI(
    title="Steam DB",
    version="0.0.1",
    license_info={
        "name": "MIT",
        "url": "https://github.com/P90Master/steamdb/blob/main/LICENSE",
    },
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ReplaceQueryParamsMiddleware)  # type: ignore
app.add_middleware(AuthMiddleware)  # type: ignore
app.add_middleware(ExceptionHandlerMiddleware)  # type: ignore


from app.api import api_router

app.include_router(api_router)
