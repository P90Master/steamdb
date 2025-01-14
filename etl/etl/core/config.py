import warnings
from typing_extensions import Self

from pydantic import (
    AnyUrl,
    computed_field,
    model_validator,
    MongoDsn,
    RedisDsn,
)

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEBUG: bool = True
    TIME_ZONE: str = 'Europe/Moscow'
    USE_TZ: bool = True
    BATCH_SIZE: int = 100

    LOGGER_WRITE_IN_FILE: bool = True
    LOGGER_LOG_FILES_PATH: str = 'logs'

    MONGO_HOST: str = 'mongodb'
    MONGO_PORT: int = 27017
    MONGO_DB: str = 'apps'
    MONGO_COLLECTION: str = 'apps'
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

    STATE_STORAGE_HOST: str = 'localhost'
    STATE_STORAGE_PORT: int = 6379
    STATE_STORAGE_PROTOCOL: str = 'redis'
    STATE_STORAGE_PASSWORD: str = 'CHANGE-ME'

    @computed_field
    @property
    def STATE_STORAGE_URL(self) -> str:  # type: ignore
        if self.STATE_STORAGE_PROTOCOL == 'redis':
            return RedisDsn.build(
                scheme='redis',
                host=self.STATE_STORAGE_HOST,
                port=self.STATE_STORAGE_PORT,
                password=self.STATE_STORAGE_PASSWORD,
            ).unicode_string()

        return AnyUrl.build(
            scheme=self.STATE_STORAGE_PROTOCOL,
            host=self.STATE_STORAGE_HOST,
            port=self.STATE_STORAGE_PORT,
        ).unicode_string()

    ELASTICSEARCH_HOST: str = 'ftsearch-index'
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_USER: str = 'elastic'
    ELASTICSEARCH_PASSWORD: str = 'CHANGE-ME'
    ELASTICSEARCH_INDEX: str = 'steam-apps'
    ELASTICSEARCH_INDEX_PATH: str = 'es_index.json'

    @computed_field
    @property
    def ELASTICSEARCH_URL(self) -> str:  # type: ignore
        return AnyUrl.build(
            scheme='http',
            host=self.ELASTICSEARCH_HOST,
            port=self.ELASTICSEARCH_PORT,
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
        self._check_default_secret('STATE_STORAGE_PASSWORD', self.STATE_STORAGE_PASSWORD)
        return self

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        env_ignore_empty = True


settings = Settings()
