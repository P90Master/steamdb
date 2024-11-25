from fastapi import FastAPI, APIRouter

from .routers import task_router


app = FastAPI()

common_api_router = APIRouter(prefix='/api', tags=['API'])
api_v1_router = APIRouter(prefix='/v1', tags=['API v1'])
api_v1_router.include_router(common_api_router)

task_router.include_router(api_v1_router)

app.include_router(task_router)
