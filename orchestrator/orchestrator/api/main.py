from fastapi import FastAPI, APIRouter

from orchestrator.config import settings
from .routers import task_router


app = FastAPI()

api_v1_router = APIRouter(prefix=f'/{settings.API_VERSION}', tags=[f'API {settings.API_VERSION}'])
api_v1_router.include_router(task_router)
common_api_router = APIRouter(prefix='/api', tags=['API'])
common_api_router.include_router(api_v1_router)

app.include_router(common_api_router)
