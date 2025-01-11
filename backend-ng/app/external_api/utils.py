import asyncio
import functools
from time import sleep
from typing import Literal, Any

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

            except AuthenticationError as auth_error:
                logger.error(
                    f"Received authentication error. Status code: {auth_error}."
                )
                raise auth_error

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

            except AuthenticationError as auth_error:
                logger.error(
                    f"Received authentication error. Status code: {auth_error}."
                )
                raise auth_error

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
