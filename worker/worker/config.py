from enum import Enum

from pydantic_settings import BaseSettings


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

    BACKEND_PROTOCOL: str = "http"
    BACKEND_HOST: str = "backend"
    BACKEND_PORT: int = 8000
    # TODO: advanced URL builder (like validator func)
    BACKEND_URL: str = f'{BACKEND_PROTOCOL}://{BACKEND_HOST}:{BACKEND_PORT}'
    BACKEND_API_VERSION: str = 'v1'

    STEAM_APP_LIST_URL: str = 'http://api.steampowered.com/ISteamApps/GetAppList/v2'
    STEAM_APP_DETAIL_URL: str = 'http://store.steampowered.com/api/appdetails'

    LOGGER_WRITE_IN_FILE: bool = True
    LOGGER_LOG_FILES_PATH: str = 'logs'

    CELERY_NAME: str = "requests_to_steam"
    CELERY_BROKER_HOST: str = "worker-celery-broker"
    CELERY_BROKER_PORT: int = 6379
    CELERY_BROKER_PROTOCOL: str = "redis"
    # TODO: advanced URL builder (like validator func)
    CELERY_BROKER_URL: str = f"{CELERY_BROKER_PROTOCOL}://{CELERY_BROKER_HOST}:{CELERY_BROKER_PORT}/0"
    CELERY_BROKER: str = CELERY_BROKER_URL
    CELERY_BACKEND: str = CELERY_BROKER_URL
    # TODO: validate by max 40/m - steam api limit
    CELERY_TASK_COMMON_RATE_LIMIT: str = '39/m'
    CELERY_TASK_TIME_LIMIT: int = 20

    RABBITMQ_HOST: str = 'orchestrator-worker-broker'
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = 'user'
    RABBITMQ_PASSWORD: str = 'password'
    RABBITMQ_INCOME_QUERY: str = 'tasks_for_workers'
    RABBITMQ_OUTCOME_QUERY: str = 'tasks_for_orchestrator'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = WorkerSettings()
