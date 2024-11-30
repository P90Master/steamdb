from enum import Enum

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

    DB_HOST: str = 'orchestrator-db'
    DB_PORT: int = 5432
    DB_TYPE: str = 'postgresql'
    DB_DRIVER: str = 'psycopg'
    DB_USER: str = 'user'
    DB_PASSWORD: str = 'password'
    DB_NAME: str = 'steam_apps'
    # TODO: advanced URL builder (like validator func)
    DB_URL: str = f"{DB_TYPE}+{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

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
    # TODO: advanced URL builder (like validator func)
    CELERY_BROKER_URL: str = f"{CELERY_BROKER_PROTOCOL}://{CELERY_BROKER_HOST}:{CELERY_BROKER_PORT}/0"
    CELERY_BROKER: str = CELERY_BROKER_URL
    CELERY_BACKEND: str = CELERY_BROKER_URL
    CELERY_TASK_TIME_LIMIT: int = 1800
    CELERY_SCHEDULE_REQUEST_ACTUAL_APP_LIST: str = '*/5 * * * *'
    CELERY_SCHEDULE_REQUEST_FOR_APPS_DATA: str = '*/5 * * * *'

    LOGGER_WRITE_IN_FILE: bool = True
    LOGGER_LOG_FILES_PATH: str = 'logs'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = OrchestratorSettings()
