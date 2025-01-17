from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class ReplaceQueryParamsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        query_string = request.scope['query_string'].decode()

        if query_string:
            new_query_string = query_string.replace('+', '%2B')
            request.scope['query_string'] = new_query_string.encode()

        return await call_next(request)
