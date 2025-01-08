from typing import Any

from fastapi import Request, HTTPException
import httpx
from starlette.middleware.base import BaseHTTPMiddleware

from orchestrator.core.config import settings
from app.utils.cache import CacheManager


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: callable):
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            request.state.user = {}
            return await call_next(request)

        token_type, _, token = authorization.partition(" ")
        if token_type.lower() != "bearer" or not token:
            raise HTTPException(status_code=401, detail="Invalid authorization code")

        token_info = await self.verify_token(token)
        request.state.user = {"id": token_info.get("client_id"), "scopes": token_info.get("scopes")}
        return await call_next(request)

    async def verify_token(self, token: str) -> dict[str, Any]:
        cache_key = f'token_{token}'
        cached_app_data = await CacheManager.get(cache_key)

        if cached_app_data:
            return cached_app_data

        async with httpx.AsyncClient() as client:
            response = await client.post(settings.OAUTH2_SERVER_URL, json={"access_token": token})

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))

            token_info = response.json()
            await CacheManager.save(response.json(), cache_key, expire=300)
            return token_info
