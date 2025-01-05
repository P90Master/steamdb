import warnings
from typing_extensions import Self

from pydantic import model_validator, computed_field, PostgresDsn, AnyUrl, RedisDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEBUG: bool = True
    API_VERSION: str = 'oauth2'
    TIME_ZONE: str = 'Europe/Moscow'
    USE_TZ: bool = True
    SUPERUSER_USERNAME: str = 'admin'
    SUPERUSER_PASSWORD: str = 'CHANGE-ME'

    ESSENTIAL_BACKEND_CLIENT_ID: str = 'backend'
    ESSENTIAL_BACKEND_CLIENT_SECRET: str = 'CHANGE-ME'
    ESSENTIAL_WORKER_CLIENT_ID: str = 'worker'
    ESSENTIAL_WORKER_CLIENT_SECRET: str = 'CHANGE-ME'

    ACCESS_TOKEN_BYTES_LENGTH: int = 16
    REFRESH_TOKEN_BYTES_LENGTH: int = 32
    ADMIN_TOKEN_BYTES_LENGTH: int = 32
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 86400
    ADMIN_TOKEN_EXPIRE_SECONDS: int = 86400
    MAX_ACCESS_TOKENS_PER_CLIENT: int = 10
    # TOKEN_TYPE: str = 'Bearer'

    DB_HOST: str = 'auth-db'
    DB_PORT: int = 5432
    DB_TYPE: str = 'postgresql'
    DB_DRIVER: str = 'psycopg'
    DB_USER: str = 'postgres'
    DB_PASSWORD: str = 'postgres'
    DB_NAME: str = 'auth'

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

    CELERY_NAME: str = "scheduled_tasks"
    CELERY_BROKER_HOST: str = "auth-task-broker"
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
    CELERY_SCHEDULE_CLEAN_EXPIRED_TOKENS: str = '0 */2 * * *'

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
        self._check_default_secret('SUPERUSER_PASSWORD', self.SUPERUSER_PASSWORD)
        self._check_default_secret('ESSENTIAL_BACKEND_CLIENT_SECRET', self.ESSENTIAL_BACKEND_CLIENT_SECRET)
        self._check_default_secret('ESSENTIAL_WORKER_CLIENT_SECRET', self.ESSENTIAL_WORKER_CLIENT_SECRET)
        self._check_default_secret('DB_PASSWORD', self.DB_PASSWORD)
        return self

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        env_ignore_empty = True


settings = Settings()
