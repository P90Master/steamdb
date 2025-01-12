import asyncio
import functools
from time import sleep
from typing import Any

from httpx import HTTPStatusError, ConnectError, ConnectTimeout

from app.core.config import settings
from app.core.logger import get_logger


class APIClientException(Exception):
    pass


class AuthenticationError(Exception):
    pass


DEFAULT_EXCEPTIONS_FOR_RETRY = (
    HTTPStatusError,
    ConnectError,
    ConnectTimeout,
    APIClientException,
)

logger = get_logger(settings, 'external_api')


def retry(timeout: int = 5, attempts: int = 2, request_exceptions: tuple[Exception] | None = None) -> callable:
    if not request_exceptions:
        request_exceptions = DEFAULT_EXCEPTIONS_FOR_RETRY

    def decorator(decorated: callable) -> callable:
        @functools.wraps(decorated)
        async def async_wrapper(cls, *args, **kwargs) -> Any:
            attempts_counter = attempts

            while True:
                try:
                    return await decorated(cls, *args, **kwargs)

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
        def sync_wrapper(cls, *args, **kwargs) -> Any:
            attempts_counter = attempts

            while True:
                try:
                    return decorated(cls, *args, **kwargs)

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
