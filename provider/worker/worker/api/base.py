import abc
import asyncio
import functools

import aiohttp

from worker.logger import logger


class APIClientException(Exception):
    pass


def handle_response_exceptions(component=__name__, method=None, url=None):
    def decorator(coro):
        @functools.wraps(coro)
        async def wrapper(*args, **kwargs):
            try:
                return await coro(*args, **kwargs)

            except aiohttp.ClientResponseError as http_error:
                logger.error(
                    f"Received {http_error.status} from {component}."
                    f" URL: {url or 'Not specified'}"
                    f" Method: {method or 'Not specified'}"
                    f" Error: {http_error}"
                )
                # TODO raise for failed requests accounting

            except Exception as unknown_error:
                logger.error(
                    f"Unhandled exception received: {unknown_error}"
                    f" URL: {url or 'Not specified'}"
                    f" Method: {method or 'Not specified'}"
                )

        return wrapper

    return decorator


class BaseSessionClient(abc.ABC):
    SESSION_CLASS = NotImplemented

    def __init__(self, *args, **kwargs):
        self._session = self.SESSION_CLASS(*args, **kwargs)

    async def close(self):
        await self._session.close()


class BaseAPIClient(abc.ABC):
    SESSION_CLIENT = BaseSessionClient
    SESSION_CLIENT_FOR_SINGLE_REQUESTS = NotImplemented
    API_CLIENT_EXCEPTION_CLASS = APIClientException

    def __init__(self, token):
        self._token = token
        self._session = None
        self._session_client = self.SESSION_CLIENT
        self._session_lock = asyncio.Lock()
        self._session_consumers_counter = 0

    async def __aenter__(self, *args, **kwargs):
        async with self._session_lock:
            self._session_consumers_counter += 1

            if self._session_consumers_counter == 1:
                self._session = self._session_client(*args, **kwargs)
                return self._session

            if self._session is None:
                raise self.API_CLIENT_EXCEPTION_CLASS('Session has readers, but has not been initialized')

            return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # TODO Handle if exc_type is not None

        async with self._session_lock:
            self._session_consumers_counter -= 1

            if self._session_consumers_counter == 0:
                await self._session.close()
                self._session = None

            return False