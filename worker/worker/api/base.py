import abc
import asyncio
import functools
from time import sleep
from types import TracebackType
from typing import Literal, Any, Type

import aiohttp
import requests

from worker.core.config import settings
from worker.core.logger import get_logger


logger = get_logger(settings)


class APIClientException(Exception):
    pass


DEFAULT_EXCEPTIONS_FOR_RETRY = (
    aiohttp.client_exceptions.ClientResponseError,
    aiohttp.client_exceptions.ClientConnectionError,
    requests.exceptions.RequestException,
    requests.exceptions.HTTPError,
    APIClientException,
)

DEFAULT_HANDLEABLE_EXCEPTIONS = (
    requests.exceptions.RequestException,
)

DEFAULT_HANDLEABLE_ASYNC_EXCEPTIONS = (
    aiohttp.ClientResponseError,
)


def handle_response_exceptions(
        component: str = __name__,
        method: Literal["GET", "POST", "PUT", "DELETE"] | None = None,
        url: str | None = None
)-> callable:
    def decorator(decorated: callable) -> callable:
        @functools.wraps(decorated)
        async def async_wrapper(*args, **kwargs) -> any:
            try:
                return await decorated(*args, **kwargs)

            except DEFAULT_HANDLEABLE_ASYNC_EXCEPTIONS as http_error:
                logger.error(
                    f"Received handleable exception from {component}."
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

        @functools.wraps(decorated)
        def sync_wrapper(*args, **kwargs):
            try:
                return decorated(*args, **kwargs)

            except DEFAULT_HANDLEABLE_EXCEPTIONS as http_error:
                logger.error(
                    f"Received handleable exception from {component}."
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

        return async_wrapper if asyncio.iscoroutinefunction(decorated) else sync_wrapper

    return decorator


def retry(timeout: int = 5, attempts: int = 2, request_exceptions: tuple[Exception] | None = None) -> callable:
    if not request_exceptions:
        request_exceptions = DEFAULT_EXCEPTIONS_FOR_RETRY

    def decorator(decorated: callable) -> callable:
        @functools.wraps(decorated)
        async def async_wrapper(*args, **kwargs) -> Any:
            attempts_counter = attempts

            while True:
                try:
                    return await decorated(*args, **kwargs)

                except request_exceptions as request_error:
                    if attempts_counter > 0:
                        attempts_counter -= 1
                        logger.warning(
                            f"Request by method {decorated.__name__}() failed. Error: {request_error}."
                            f" Retries left: {attempts_counter}"
                        )
                        await asyncio.sleep(timeout)

                    else:
                        raise request_error

        @functools.wraps(decorated)
        def sync_wrapper(*args, **kwargs) -> Any:
            attempts_counter = attempts

            while True:
                try:
                    return decorated(*args, **kwargs)

                except request_exceptions as request_error:
                    if attempts_counter > 0:
                        attempts_counter -= 1
                        logger.warning(
                            f"Request by method {decorated.__name__}() failed. Error: {request_error}."
                            f" Retries left: {attempts_counter}"
                        )
                        sleep(timeout)

                    else:
                        raise request_error

        return async_wrapper if asyncio.iscoroutinefunction(decorated) else sync_wrapper

    return decorator


class BaseAsyncSessionClient(abc.ABC):
    SESSION_CLASS = ...

    def __init__(self, *args, **kwargs):
        self._session = self.SESSION_CLASS(*args, **kwargs)

    async def close(self):
        await self._session.close()


class BaseAsyncAPIClient(abc.ABC):
    SESSION_CLIENT = BaseAsyncSessionClient
    SESSION_CLIENT_FOR_SINGLE_REQUESTS = ...
    API_CLIENT_EXCEPTION_CLASS = APIClientException

    def __init__(self, token: str | None = None):
        self._token: str | None = token
        self._session: BaseAsyncSessionClient | None = None
        self._session_client: Type[BaseAsyncSessionClient] = self.SESSION_CLIENT
        self._session_lock: asyncio.Lock = asyncio.Lock()
        self._session_consumers_counter: int = 0

    async def __aenter__(self, *args, **kwargs) -> BaseAsyncSessionClient:
        async with self._session_lock:
            self._session_consumers_counter += 1

            if self._session_consumers_counter == 1:
                self._session = self._session_client(*args, **kwargs)
                return self._session

            if self._session is None:
                raise self.API_CLIENT_EXCEPTION_CLASS('Session has readers, but has not been initialized')

            return self._session

    async def __aexit__(
            self,
            exc_type: Type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None
    ) -> bool | None:
        async with self._session_lock:
            self._session_consumers_counter -= 1

            if self._session_consumers_counter == 0:
                await self._session.close()
                self._session = None

        return False
