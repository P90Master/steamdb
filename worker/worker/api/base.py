import abc
import asyncio
import functools
from typing import Callable

import aiohttp

from worker.logger import logger


class APIClientException(Exception):
    pass


DEFAULT_EXCEPTIONS_FOR_RETRY = (
    aiohttp.ClientResponseError,
    aiohttp.ClientConnectionError,
    APIClientException,
)


def handle_response_exceptions(component=__name__, method=None, url=None)-> Callable:
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
                raise http_error

            except Exception as unknown_error:
                logger.error(
                    f"Unhandled exception received: {unknown_error}"
                    f" URL: {url or 'Not specified'}"
                    f" Method: {method or 'Not specified'}"
                )
                raise unknown_error

        return wrapper

    return decorator


def retry(timeout: int = 5, attempts: int = 2, request_exceptions: tuple[Exception] = None) -> Callable:
    if not request_exceptions:
        request_exceptions = DEFAULT_EXCEPTIONS_FOR_RETRY

    def decorator(coro):
        @functools.wraps(coro)
        async def wrapper(*args, **kwargs):
            attempts_counter = attempts

            while True:
                try:
                    return await coro(*args, **kwargs)

                except request_exceptions as request_error:
                    if attempts_counter > 0:
                        attempts_counter -= 1
                        logger.warning(
                            f"Request by method {coro.__name__}() failed. Error: {request_error}."
                            f" Retries left: {attempts_counter}"
                        )
                        await asyncio.sleep(timeout)

                    else:
                        raise request_error

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
        async with self._session_lock:
            self._session_consumers_counter -= 1

            if self._session_consumers_counter == 0:
                await self._session.close()
                self._session = None

        return False
