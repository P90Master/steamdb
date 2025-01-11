import warnings
from typing import Self

from pydantic import field_validator, computed_field, RedisDsn, AnyUrl, model_validator
from pydantic_settings import BaseSettings

from worker.core.enums import CountryCodes


class WorkerSettings(BaseSettings):
    DEFAULT_COUNTRY_CODE: str = CountryCodes.united_states.value
    # TODO: convert from string to list
    DEFAULT_COUNTRY_BUNDLE: list[str] = [
        CountryCodes.united_states.value,
        CountryCodes.united_kingdom.value,
        CountryCodes.china.value,
        CountryCodes.russia.value,
        CountryCodes.germany.value,
        CountryCodes.japan.value,
        CountryCodes.brazil.value,
    ]
    DEBUG: bool = True
    TIME_ZONE: str = 'Europe/Moscow'
    USE_TZ: bool = True

    ESSENTIAL_WORKER_CLIENT_ID: str = 'worker'
    ESSENTIAL_WORKER_CLIENT_SECRET: str = 'CHANGE-ME'
    ESSENTIAL_WORKER_CLIENT_SCOPES: list[str] = [
        'backend/package'
    ]
    OAUTH2_SERVER_HOST: str = 'localhost'
    OAUTH2_SERVER_PORT: int = 8001
    OAUTH2_SERVER_PROTOCOL: str = 'http'

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

    BACKEND_PROTOCOL: str = "http"
    BACKEND_HOST: str = "backend"
    BACKEND_PORT: int = 8000
    BACKEND_API_VERSION: str = 'v1'

    @computed_field
    @property
    def BACKEND_PACKAGE_ENDPOINT_URL(self) -> str:  # type: ignore
        return AnyUrl.build(
            scheme=self.BACKEND_PROTOCOL,
            host=self.BACKEND_HOST,
            port=self.BACKEND_PORT,
            path=f'api/{settings.BACKEND_API_VERSION}/package',
        ).unicode_string()

    STEAM_APP_LIST_URL: str = 'http://api.steampowered.com/ISteamApps/GetAppList/v2'
    STEAM_APP_DETAIL_URL: str = 'http://store.steampowered.com/api/appdetails'

    LOGGER_WRITE_IN_FILE: bool = True
    LOGGER_LOG_FILES_PATH: str = '../logs'

    CELERY_NAME: str = "requests_to_steam"
    CELERY_BROKER_HOST: str = "worker-celery-broker"
    CELERY_BROKER_PORT: int = 6379
    CELERY_BROKER_PROTOCOL: str = "redis"
    CELERY_TASK_COMMON_RATE_LIMIT: str = '39/m'
    CELERY_TASK_TIME_LIMIT: int = 40

    @computed_field
    @property
    def CELERY_BROKER_URL(self) -> str:  # type: ignore
        if self.CELERY_BROKER_PROTOCOL == 'redis':
            return RedisDsn.build(
                scheme='redis',
                host=self.CELERY_BROKER_HOST,
                port=self.CELERY_BROKER_PORT,
            ).unicode_string()

        return AnyUrl.build(
            scheme=self.CELERY_BROKER_PROTOCOL,
            host=self.CELERY_BROKER_HOST,
            port=self.CELERY_BROKER_PORT,
        ).unicode_string()

    @computed_field
    @property
    def CELERY_BROKER(self) -> str:  # type: ignore
        return self.CELERY_BROKER_URL

    @computed_field
    @property
    def CELERY_BACKEND(self) -> str:  # type: ignore
        return self.CELERY_BROKER_URL

    RABBITMQ_HOST: str = 'orchestrator-worker-broker'
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = 'user'
    RABBITMQ_PASSWORD: str = 'password'
    RABBITMQ_INCOME_QUERY: str = 'tasks_for_workers'
    RABBITMQ_OUTCOME_QUERY: str = 'tasks_for_orchestrator'
    RABBITMQ_CONNECTION_ATTEMPTS: int = 3
    RABBITMQ_CONNECTION_RETRY_DELAY: int = 3
    RABBITMQ_HEARTBEATS_TIMEOUT: int = 30
    RABBITMQ_HEARTBEATS_MAX_DELAY: int = 120

    @field_validator("CELERY_TASK_COMMON_RATE_LIMIT")
    @classmethod
    def validate_employee_id(cls, v: str, info):
        if not v.endswith('/m'):
            raise ValueError("Rate limit must end with '/m'")

        try:
            limit = int(v[:-2])
        except ValueError:
            raise ValueError("Rate limit must be a valid integer followed by '/m'")

        if limit < 1 or limit > 40:
            raise ValueError("Rate limit must be between '1/m' and '40/m'")

        return v

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == 'CHANGE-ME':
            message = f'The {var_name} needs real value instead of "CHANGE-ME".'

            if self.DEBUG:
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode='after')
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret('ESSENTIAL_WORKER_CLIENT_SECRET', self.ESSENTIAL_WORKER_CLIENT_SECRET)
        return self

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = WorkerSettings()
