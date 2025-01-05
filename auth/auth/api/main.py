from fastapi import APIRouter

from auth.api.routers import auth_router
from auth.core.config import settings


api_oauth2_router = APIRouter(prefix=f'/{settings.API_VERSION}', tags=[f'API {settings.API_VERSION}'])
api_oauth2_router.include_router(auth_router)

api_router = APIRouter(prefix='/api')
api_router.include_router(api_oauth2_router)
