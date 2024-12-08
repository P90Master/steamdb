from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    DEBUG: bool = True
    API_VERSION: str = 'v1'
    ACCESS_TOKEN_BYTES_LENGTH: int = 16
    REFRESH_TOKEN_BYTES_LENGTH: int = 32
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 86400
    MAX_ACCESS_TOKENS_PER_CLIENT: int = 10

    DB_HOST: str = 'auth-db'
    DB_PORT: int = 5432
    DB_TYPE: str = 'postgresql'
    DB_DRIVER: str = 'psycopg'
    DB_USER: str = 'postgres'
    DB_PASSWORD: str = 'postgres'
    DB_NAME: str = 'auth'
    # TODO: advanced URL builder PostgresDsn
    DB_URL: str = f"{DB_TYPE}+{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    LOGGER_WRITE_IN_FILE: bool = True
    LOGGER_LOG_FILES_PATH: str = 'logs'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = AuthSettings()
