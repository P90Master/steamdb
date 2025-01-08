from fastapi import FastAPI, APIRouter

from orchestrator.api.middlewares import AuthMiddleware, ExceptionHandlerMiddleware
from orchestrator.core.config import settings
from orchestrator.api.routers import task_router


app = FastAPI()

app.add_middleware(AuthMiddleware)  # type: ignore
app.add_middleware(ExceptionHandlerMiddleware)  # type: ignore

api_v1_router = APIRouter(prefix=f'/{settings.API_VERSION}', tags=[f'API {settings.API_VERSION}'])
api_v1_router.include_router(task_router)
common_api_router = APIRouter(prefix='/api', tags=['API'])
common_api_router.include_router(api_v1_router)

app.include_router(common_api_router)
