import warnings
from typing import Self

from pydantic import computed_field, PostgresDsn, RedisDsn, AnyUrl, model_validator
from pydantic_settings import BaseSettings

from .enums import CountryCodes


class OrchestratorSettings(BaseSettings):
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
    BATCH_SIZE_OF_UPDATING_STEAM_APPS: int = 20
    DB_INPUT_BATCH_SIZE: int = 1000
    DEBUG: bool = True
    API_VERSION: str = 'v1'
    TIME_ZONE: str = 'Europe/Moscow'
    USE_TZ: bool = True
    SCHEDULED_TASKS_PRIORITY: int = 1
    TASKS_FROM_API_PRIORITY: int = 3

    DB_HOST: str = 'orchestrator-db'
    DB_PORT: int = 5432
    DB_TYPE: str = 'postgresql'
    DB_DRIVER: str = 'psycopg'
    DB_USER: str = 'user'
    DB_PASSWORD: str = 'password'
    DB_NAME: str = 'steam_apps'

    @computed_field
    @property
    def DB_URL(self) -> str:  # type: ignore
        return PostgresDsn.build(
            scheme=f'{self.DB_TYPE}+{self.DB_DRIVER}',
            host=self.DB_HOST,
            port=self.DB_PORT,
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            path=self.DB_NAME
        ).unicode_string()

    RABBITMQ_HOST: str = 'orchestrator-worker-broker'
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = 'user'
    RABBITMQ_PASSWORD: str = 'password'
    RABBITMQ_INCOME_QUERY: str = 'tasks_for_orchestrator'
    RABBITMQ_OUTCOME_QUERY: str = 'tasks_for_workers'
    RABBITMQ_CONNECTION_ATTEMPTS: int = 3
    RABBITMQ_CONNECTION_RETRY_DELAY: int = 3
    RABBITMQ_HEARTBEATS_MAX_DELAY: int = 120
    RABBITMQ_HEARTBEATS_TIMEOUT: int = 30

    CELERY_NAME: str = "scheduled_tasks"
    CELERY_BROKER_HOST: str = "orchestrator-task-broker"
    CELERY_BROKER_PORT: int = 6379
    CELERY_BROKER_PROTOCOL: str = "redis"

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

    CELERY_TASK_TIME_LIMIT: int = 1800
    CELERY_SCHEDULE_REQUEST_ACTUAL_APP_LIST: str = '*/5 * * * *'
    CELERY_SCHEDULE_REQUEST_FOR_APPS_DATA: str = '*/5 * * * *'

    LOGGER_WRITE_IN_FILE: bool = True
    LOGGER_LOG_FILES_PATH: str = 'logs'

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == 'CHANGE-ME':
            message = f'The {var_name} needs real value instead of "CHANGE-ME".'

            if self.DEBUG:
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode='after')
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret('RABBITMQ_PASSWORD', self.RABBITMQ_PASSWORD)
        self._check_default_secret('DB_PASSWORD', self.DB_PASSWORD)
        return self

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        env_ignore_empty = True


settings = OrchestratorSettings()
