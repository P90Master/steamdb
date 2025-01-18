import warnings
from typing import Annotated, Any
from typing_extensions import Self

from pydantic import (
    AnyUrl,
    BeforeValidator,
    computed_field,
    model_validator,
    MongoDsn,
    RedisDsn,
)

from pydantic_settings import BaseSettings


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith('['):
        return [i.strip() for i in v.split(',')]

    if isinstance(v, list | str):
        return v

    raise ValueError(v)


class Settings(BaseSettings):
    DEBUG: bool = True
    API_VERSION: str = 'v1'
    TIME_ZONE: str = 'Europe/Moscow'
    USE_TZ: bool = True
    MAIN_COUNTRY: str = 'US'

    ESSENTIAL_BACKEND_CLIENT_ID: str = 'backend'
    ESSENTIAL_BACKEND_CLIENT_SECRET: str = 'CHANGE-ME'
    ESSENTIAL_BACKEND_CLIENT_SCOPES: list[str] = [
        'orchestrator/tasks'
    ]
    OAUTH2_SERVER_HOST: str = 'localhost'
    OAUTH2_SERVER_PORT: int = 8001
    OAUTH2_SERVER_PROTOCOL: str = 'http'

    LOGGER_WRITE_IN_FILE: bool = False
    LOGGER_LOG_FILES_PATH: str = 'logs'

    @computed_field
    @property
    def OAUTH2_SERVER_INTROSPECT_URL(self) -> str:  # type: ignore
        return AnyUrl.build(
            scheme=self.OAUTH2_SERVER_PROTOCOL,
            host=self.OAUTH2_SERVER_HOST,
            port=self.OAUTH2_SERVER_PORT,
            path='api/oauth2/introspect',
        ).unicode_string()

    @computed_field
    @property
    def OAUTH2_SERVER_LOGIN_URL(self) -> str:  # type: ignore
        return AnyUrl.build(
            scheme=self.OAUTH2_SERVER_PROTOCOL,
            host=self.OAUTH2_SERVER_HOST,
            port=self.OAUTH2_SERVER_PORT,
            path='api/oauth2/token',
        ).unicode_string()

    @computed_field
    @property
    def OAUTH2_SERVER_REFRESH_TOKEN_URL(self) -> str:  # type: ignore
        return AnyUrl.build(
            scheme=self.OAUTH2_SERVER_PROTOCOL,
            host=self.OAUTH2_SERVER_HOST,
            port=self.OAUTH2_SERVER_PORT,
            path='api/oauth2/token_refresh',
        ).unicode_string()

    FRONTEND_HOST: str = 'http://localhost:3000'
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field
    @property
    def ALLOWED_HOSTS(self) -> list[str]:  # type: ignore
        return [str(origin).rstrip('/') for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    MONGO_HOST: str = 'mongodb'
    MONGO_PORT: int = 27017
    MONGO_DB: str = 'apps'
    MONGO_USER: str = 'admin'
    MONGO_PASSWORD: str = 'admin'

    @computed_field
    @property
    def MONGO_URL(self) -> str:  # type: ignore
        return MongoDsn.build(
            scheme='mongodb',
            host=self.MONGO_HOST,
            port=self.MONGO_PORT,
            username=self.MONGO_USER,
            password=self.MONGO_PASSWORD
        ).unicode_string()

    CACHE_TIMEOUT: int = 60 * 20
    CACHE_PREFIX: str = 'backend-cache'
    CACHE_HOST: str = 'localhost'
    CACHE_PORT: int = 6379
    CACHE_PROTOCOL: str = 'redis'

    @computed_field
    @property
    def CACHE_URL(self) -> str:  # type: ignore
        if self.CACHE_PROTOCOL == 'redis':
            return RedisDsn.build(
                scheme='redis',
                host=self.CACHE_HOST,
                port=self.CACHE_PORT,
            ).unicode_string()

        return AnyUrl.build(
            scheme=self.CACHE_PROTOCOL,
            host=self.CACHE_HOST,
            port=self.CACHE_PORT,
        ).unicode_string()

    ELASTICSEARCH_HOST: str = 'ftsearch-index'
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_USER: str = 'elastic'
    ELASTICSEARCH_PASSWORD: str = 'CHANGE-ME'
    ELASTICSEARCH_INDEX: str = 'steam-apps'

    @computed_field
    @property
    def ELASTICSEARCH_URL(self) -> str:  # type: ignore
        return AnyUrl.build(
            scheme='http',
            host=self.ELASTICSEARCH_HOST,
            port=self.ELASTICSEARCH_PORT,
        ).unicode_string()

    ORCHESTRATOR_HOST: str = 'orchestrator'
    ORCHESTRATOR_PORT: int = 8888
    ORCHESTRATOR_PROTOCOL: str = 'http'
    ORCHESTRATOR_API_VERSION: str = 'v1'

    @computed_field
    @property
    def ORCHESTRATOR_TASKS_API_URL(self) -> str:  # type: ignore
        return AnyUrl.build(
            scheme=self.ORCHESTRATOR_PROTOCOL,
            host=self.ORCHESTRATOR_HOST,
            port=self.ORCHESTRATOR_PORT,
            path=f'api/{self.ORCHESTRATOR_API_VERSION}/tasks/',
        ).unicode_string()

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == 'CHANGE-ME':
            message = f'The {var_name} needs real value instead of "CHANGE-ME".'

            if self.DEBUG:
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode='after')
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret('MONGO_PASSWORD', self.MONGO_PASSWORD)
        self._check_default_secret('ELASTICSEARCH_PASSWORD', self.ELASTICSEARCH_PASSWORD)
        self._check_default_secret('ESSENTIAL_BACKEND_CLIENT_SECRET', self.ESSENTIAL_BACKEND_CLIENT_SECRET)
        return self

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        env_ignore_empty = True


settings = Settings()
