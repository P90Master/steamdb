from fastapi import APIRouter

# from auth.api.routers import app_router, package_router
from auth.core.config import settings


api_v1_router = APIRouter(prefix=f'/{settings.API_VERSION}', tags=[f'API {settings.API_VERSION}'])
#api_v1_router.include_router(app_router)
#api_v1_router.include_router(package_router)

api_router = APIRouter(prefix='/api')
api_router.include_router(api_v1_router)
