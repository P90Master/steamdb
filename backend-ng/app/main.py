from contextlib import asynccontextmanager

from fastapi import FastAPI
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.models import DOCUMENTS
from app.middlewares import ReplaceQueryParamsMiddleware


@asynccontextmanager
async def lifespan(app_: FastAPI):
    app_.db_client = getattr(AsyncIOMotorClient(settings.MONGO_URL), settings.MONGO_DB)
    await init_beanie(app_.db_client, document_models=DOCUMENTS)

    yield

    app_.db_client.close()


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


from app.api import api_router

app.include_router(api_router)
