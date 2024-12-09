import secrets
import warnings
from typing import Annotated, Any

from pydantic import (
    AnyUrl,
    BeforeValidator,
    computed_field,
    model_validator,
    MongoDsn,
)

from pydantic_settings import BaseSettings
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith('['):
        return [i.strip() for i in v.split(',')]

    if isinstance(v, list | str):
        return v

    raise ValueError(v)


class Settings(BaseSettings):
    DEBUG: bool = True
    API_VERSION: str = 'v1'
    SECRET_KEY: str = secrets.token_urlsafe(32)

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

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == 'CHANGE-ME':
            message = f'The {var_name} needs real value instead of "CHANGE-ME".'

            if self.DEBUG:
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode='after')
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret('SECRET_KEY', self.SECRET_KEY)
        self._check_default_secret('MONGO_PASSWORD', self.MONGO_PASSWORD)
        return self

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        env_ignore_empty = True


settings = Settings()
