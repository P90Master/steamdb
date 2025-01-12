import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from pydantic_settings import BaseSettings


formatter = logging.Formatter("[%(name)s %(asctime)s %(levelname)s] %(message)s")
stdout_handler = logging.StreamHandler(stream=sys.stdout)
stdout_handler.setFormatter(formatter)


def get_logger(settings: BaseSettings, name: str = 'core') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.propagate = False

    if logger.hasHandlers():
        return logger

    logger.addHandler(stdout_handler)

    if settings.DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if settings.LOGGER_WRITE_IN_FILE:
        log_directory = os.path.join('auth', settings.LOGGER_LOG_FILES_PATH)

        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        log_file_path = os.path.join(log_directory, f"auth.log")
        file_handler = RotatingFileHandler(filename=log_file_path, mode='w', maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
