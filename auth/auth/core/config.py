import secrets
import warnings
from typing_extensions import Self

from pydantic import model_validator, computed_field, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEBUG: bool = True
    API_VERSION: str = 'v1'
    TIME_ZONE: str = 'Europe/Moscow'
    USE_TZ: bool = True
    SUPERUSER_USERNAME: str = 'admin'
    SUPERUSER_PASSWORD: str = secrets.token_urlsafe(16)

    ACCESS_TOKEN_BYTES_LENGTH: int = 16
    REFRESH_TOKEN_BYTES_LENGTH: int = 32
    ADMIN_TOKEN_BYTES_LENGTH: int = 32
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 86400
    ADMIN_TOKEN_EXPIRE_SECONDS: int = 86400
    MAX_ACCESS_TOKENS_PER_CLIENT: int = 10

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
        self._check_default_secret('DB_PASSWORD', self.DB_PASSWORD)
        return self

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        env_ignore_empty = True


settings = Settings()
