from enum import Enum

from pydantic import field_validator
from pydantic_settings import BaseSettings


class CountryCodes(Enum):
    united_states = "US"
    china = "CN"
    japan = "JP"
    germany = "DE"
    india = "IN"
    united_kingdom = "GB"
    france = "FR"
    italy = "IT"
    canada = "CA"
    south_korea = "KR"
    russia = "RU"
    brazil = "BR"
    australia = "AU"
    spain = "ES"
    mexico = "MX"
    indonesia = "ID"
    netherlands = "NL"
    switzerland = "CH"
    sweden = "SE"
    belgium = "BE"
    austria = "AT"
    argentina = "AR"
    norway = "NO"
    czech_republic = "CZ"


class CountryCodeSteamCurrencyMapping(Enum):
    @classmethod
    def get(cls, code):
        return cls[code].value if code in cls.__members__ else None

    US = "USD"
    CN = "CNY"
    JP = "JPY"
    DE = "EUR"
    IN = "INR"
    GB = "GBP"
    FR = "EUR"
    IT = "EUR"
    CA = "CAD"
    KR = "KRW"
    RU = "RUB"
    BR = "BRL"
    AU = "AUD"
    ES = "EUR"
    MX = "MXN"
    ID = "IDR"
    NL = "EUR"
    CH = "CHF"
    SE = "SEK"
    BE = "EUR"
    AT = "EUR"
    AR = "USD"
    NO = "NOK"
    CZ = "CZK"


class WorkerSettings(BaseSettings):
    DEFAULT_COUNTRY_CODE: str = CountryCodes.united_states.value
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
    CELERY_TASK_COMMON_RATE_LIMIT: str = '39/m'
    CELERY_TASK_TIME_LIMIT: int = 20

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

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = WorkerSettings()
