import abc

import functools
from typing import Type, ClassVar

import httpx
from httpx import HTTPStatusError

from app.core.config import settings
from .utils import APIClientException, AuthenticationError, handle_response_exceptions, retry


class BaseAsyncAPIClient(abc.ABC):
    CLIENT: Type[httpx.AsyncClient] = httpx.AsyncClient
    API_CLIENT_EXCEPTION_CLASS: Type[Exception] = APIClientException

    _client_id: ClassVar[str | None] = None
    _client_secret: ClassVar[str | None] = None
    _access_token_type: ClassVar[str | None] = None
    _access_token: ClassVar[str | None] = None
    _refresh_token: ClassVar[str | None] = None
    _init: ClassVar[bool] = False

    @classmethod
    def init(
            cls,
            client_id: str | None = None,
            client_secret: str | None = None,
            token_type: str = 'Bearer',
    ):
        cls._client_id = client_id
        cls._client_secret = client_secret
        cls._access_token_type = token_type
        cls._access_token = None
        cls._refresh_token = None
        cls._init = True

    @classmethod
    def reset(cls):
        cls._client_id = None
        cls._client_secret = None
        cls._access_token_type = 'Bearer'
        cls._access_token = None
        cls._refresh_token = None

    @classmethod
    def get_client_id(cls) -> str:
        assert cls._client_id is not None, "You must call init first!"  # noqa: S101
        return cls._client_id

    @classmethod
    def get_client_secret(cls) -> str:
        assert cls._client_secret is not None, "You must call init first!"  # noqa: S101
        return cls._client_secret

    @classmethod
    def get_access_token_type(cls) -> str:
        return cls._access_token_type

    @classmethod
    async def get_access_token(cls) -> str:
        if cls._access_token is None:
            await cls.login()

        if cls._access_token is None:
            raise AuthenticationError('Authentication to the Auth service failed')

        return cls._access_token

    @classmethod
    async def get_refresh_token(cls) -> str:
        if cls._refresh_token is None:
            await cls.login()

        if cls._refresh_token is None:
            raise AuthenticationError('Authentication to the Auth service failed')

        return cls._refresh_token


    @handle_response_exceptions(component=__name__, url=settings.OAUTH2_SERVER_LOGIN_URL, method="POST")
    @retry(timeout=10, attempts=3)
    @classmethod
    async def login(cls):
        await cls._request_for_login()

    @classmethod
    async def _request_for_login(cls):
        async with cls.CLIENT() as client:
            auth_response = await client.post(
                url=settings.OAUTH2_SERVER_LOGIN_URL,
                json={
                    'client_id': cls.get_client_id(),
                    'client_secret': cls.get_client_secret(),
                    'scopes': settings.ESSENTIAL_BACKEND_CLIENT_SCOPES,
                }
            )

            if auth_response.status_code != 200:
                if auth_response.status_code in (401, 403):
                    raise AuthenticationError(auth_response.status_code)

                raise cls.API_CLIENT_EXCEPTION_CLASS(auth_response.status_code)

            response_data = auth_response.json()
            cls._access_token = response_data['access_token']
            cls._refresh_token = response_data['refresh_token']

    @handle_response_exceptions(component=__name__, url=settings.OAUTH2_SERVER_REFRESH_TOKEN_URL, method="POST")
    @retry(timeout=10, attempts=3)
    @classmethod
    async def refresh_access_token(cls):
        await cls._request_for_refresh_access_token()

    @classmethod
    async def _request_for_refresh_access_token(cls):
        refresh_token = await cls.get_refresh_token()

        async with cls.CLIENT() as client:
            auth_response = await client.post(
                url=settings.OAUTH2_SERVER_REFRESH_TOKEN_URL,
                json={
                    'refresh_token': refresh_token,
                    'scopes': settings.ESSENTIAL_WORKER_CLIENT_SCOPES,
                }
            )

            if auth_response.status_code != 200:
                if auth_response.status_code not in (401, 403):
                    raise cls.API_CLIENT_EXCEPTION_CLASS(auth_response.status_code)

                await cls.login()
                auth_response = await client.post(
                    url=settings.OAUTH2_SERVER_REFRESH_TOKEN_URL,
                    json={
                        'refresh_token': refresh_token,
                        'scopes': settings.ESSENTIAL_WORKER_CLIENT_SCOPES,
                    }
                )
                if auth_response.status_code in (401, 403):
                    raise AuthenticationError(auth_response.status_code)

                auth_response.raise_for_status()

            response_data = auth_response.json()
            cls._access_token = response_data['access_token']


def authenticate(func: callable) -> callable:
    @functools.wraps(func)
    async def wrapper(cls: Type[BaseAsyncAPIClient], *args, **kwargs):
        access_token = await cls.get_access_token()
        access_token_type = cls.get_access_token_type()

        headers = kwargs.get('headers', {})

        try:
            headers['Authorization'] = f"{cls._access_token_type} {access_token}"
            kwargs['headers'] = headers
            return await func(cls, *args, **kwargs)

        except HTTPStatusError as error:
            if error.response.status_code in (401, 403):
                await cls.refresh_access_token()
                headers['Authorization'] = f"{access_token_type} {access_token}"
                kwargs['headers'] = headers
                try:
                    return await func(cls, *args, **kwargs)
                except HTTPStatusError as error:
                    raise AuthenticationError(error.response.status_code)

            raise error

    return wrapper
