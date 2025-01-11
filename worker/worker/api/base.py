import abc
import asyncio
import functools
from time import sleep
from types import TracebackType
from typing import Literal, Any, Type

import aiohttp
import requests
from aiohttp import ClientResponseError, ClientConnectionError

from worker.core.config import settings
from worker.core.logger import get_logger


logger = get_logger(settings, 'external_api')


class APIClientException(Exception):
    pass


class AuthenticationError(Exception):
    pass


DEFAULT_EXCEPTIONS_FOR_RETRY = (
    ClientResponseError,
    ClientConnectionError,
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

            except DEFAULT_HANDLEABLE_EXCEPTIONS as http_error:
                logger.error(
                    f"Received handleable exception from {component}."
                    f" URL: {url or 'Not specified'}"
                    f" Method: {method or 'Not specified'}"
                    f" Error: {http_error}"
                )
                raise http_error

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


class AbstractAsyncSessionClient(abc.ABC):
    SESSION_CLASS = ...

    def __init__(self, client: 'BaseAsyncAPIClient', *args, **kwargs):
        self._client = client
        self._session = self.SESSION_CLASS(*args, **kwargs)

    async def close(self):
        ...


class BaseAsyncSessionClient(AbstractAsyncSessionClient):
    SESSION_CLASS = aiohttp.ClientSession

    async def close(self):
        await self._session.close()


class BaseAsyncAPIClient(abc.ABC):
    SESSION_CLIENT = BaseAsyncSessionClient
    CLIENT_FOR_SINGLE_REQUESTS = aiohttp.ClientSession
    API_CLIENT_EXCEPTION_CLASS = APIClientException

    def __init__(self, client_id: str | None = None, client_secret: str | None = None, token_type: str = 'Bearer'):
        self.client_id: str | None = client_id
        self.client_secret: str | None = client_secret
        self.access_token_type: str = token_type
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self._session: BaseAsyncSessionClient | None = None
        self._session_client: Type[BaseAsyncSessionClient] = self.SESSION_CLIENT
        self._session_lock: asyncio.Lock = asyncio.Lock()
        self._session_consumers_counter: int = 0

    async def __aenter__(self, *args, **kwargs) -> BaseAsyncSessionClient:
        """
        Designed SPECIFICALLY to work with only 1 backend endpoint
        """

        async with self._session_lock:
            self._session_consumers_counter += 1

            if self._session_consumers_counter == 1:
                self._session = self._session_client(self, *args, **kwargs)
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

    @handle_response_exceptions(component=__name__, url=settings.OAUTH2_SERVER_LOGIN_URL, method="POST")
    @retry(timeout=10, attempts=3)
    async def login(self):
        await self._request_for_login()

    async def _request_for_login(self):
        async with self.CLIENT_FOR_SINGLE_REQUESTS() as session:
            auth_response = await session.post(
                url=settings.OAUTH2_SERVER_LOGIN_URL,
                json={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'scopes': settings.ESSENTIAL_WORKER_CLIENT_SCOPES,
                }
            )

            if auth_response.status != 200:
                if auth_response.status in (401, 403):
                    raise AuthenticationError(auth_response.status)

                raise self.API_CLIENT_EXCEPTION_CLASS(auth_response.status)

            response_data = await auth_response.json()
            self.access_token = response_data['access_token']
            self.refresh_token = response_data['refresh_token']

    @handle_response_exceptions(component=__name__, url=settings.OAUTH2_SERVER_REFRESH_TOKEN_URL, method="POST")
    @retry(timeout=10, attempts=3)
    async def refresh_access_token(self):
        await self._request_for_refresh_access_token()

    async def _request_for_refresh_access_token(self):
        if not self.refresh_token:
            await self.login()

        async with self.CLIENT_FOR_SINGLE_REQUESTS() as session:
            auth_response = await session.post(
                url=settings.OAUTH2_SERVER_REFRESH_TOKEN_URL,
                json={
                    'refresh_token': self.refresh_token,
                    'scopes': settings.ESSENTIAL_WORKER_CLIENT_SCOPES,
                }
            )

            if auth_response.status != 200:
                if auth_response.status not in (401, 403):
                    raise self.API_CLIENT_EXCEPTION_CLASS(auth_response.status)

                await self.login()
                auth_response = await session.post(
                    url=settings.OAUTH2_SERVER_REFRESH_TOKEN_URL,
                    json={
                        'refresh_token': self.refresh_token,
                        'scopes': settings.ESSENTIAL_WORKER_CLIENT_SCOPES,
                    }
                )
                if auth_response.status in (401, 403):
                    raise AuthenticationError(auth_response.status)

                auth_response.raise_for_status()

            response_data = await auth_response.json()
            self.access_token = response_data['access_token']


def authenticate(func: callable) -> callable:
    @functools.wraps(func)
    async def wrapper(self: BaseAsyncAPIClient, *args, **kwargs):
        if not (self.client_id and self.client_secret):
            raise AuthenticationError("Client ID and client secret must be set")

        if not self.access_token:
            await self.login()

        headers = kwargs.get('headers', {})

        try:
            headers['Authorization'] = f"{self.access_token_type} {self.access_token}"
            kwargs['headers'] = headers
            return await func(self, *args, **kwargs)

        except ClientResponseError as error:
            if error.status in (401, 403):
                await self.refresh_access_token()
                headers['Authorization'] = f"{self.access_token_type} {self.access_token}"
                kwargs['headers'] = headers
                try:
                    return await func(self, *args, **kwargs)
                except ClientResponseError as error:
                    raise AuthenticationError(error.status)

            raise error

    return wrapper

def authenticate_session(func: callable) -> callable:
    @functools.wraps(func)
    async def wrapper(self: BaseAsyncSessionClient, *args, **kwargs):
        client = self._client

        if not (client.client_id and client.client_secret):
            raise AuthenticationError("Client ID and client secret must be set")

        if not client.access_token:
            await client.login()

        headers = kwargs.get('headers', {})

        try:
            headers['Authorization'] = f"{client.access_token_type} {client.access_token}"
            kwargs['headers'] = headers
            return await func(self, *args, **kwargs)


        except ClientResponseError as error:
            if error.status in (401, 403):
                await client.refresh_access_token()
                headers['Authorization'] = f"{client.access_token_type} {client.access_token}"
                kwargs['headers'] = headers
                try:
                    return await func(self, *args, **kwargs)
                except ClientResponseError as error:
                    raise AuthenticationError(error.status)

            raise error

    return wrapper
