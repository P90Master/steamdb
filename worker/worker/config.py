from enum import Enum

from pydantic_settings import BaseSettings

from .logger import logger


class CountryCodes(Enum):
    united_states = 'US'
    russia = 'RU'


class CountryCodeCurrencyMapping(Enum):
    @classmethod
    def get(cls, code):
        return cls[code].value if code in cls.__members__ else None

    US = 'USD'
    RU = 'RUB'


class WorkerSettings(BaseSettings):
    DEFAULT_COUNTRY_CODE: str = CountryCodes.united_states.value
    DEBUG: bool = True
    LOGGER = logger

    BACKEND_HOST: str = 'http://backend:8000'
    BACKEND_API_VERSION: str = 'v1'

    STEAM_APP_LIST_URL: str = 'http://api.steampowered.com/ISteamApps/GetAppList/v2'
    STEAM_APP_DETAIL_URL: str = 'http://store.steampowered.com/api/appdetails'

    LOGGER_WRITE_IN_FILE: bool = True
    LOG_FILES_PATH: str = 'logs'

    # TODO: URL builder
    CELERY_NAME: str = "requests_to_steam"
    CELERY_BROKER: str = "redis://worker-celery-broker:6379/0"
    CELERY_BACKEND: str = "redis://worker-celery-broker:6379/0"
    # TODO: validate by max 40/m
    CELERY_TASK_COMMON_RATE_LIMIT: str = '39/m'
    CELERY_TASK_TIME_LIMIT: int = 20

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = WorkerSettings()
