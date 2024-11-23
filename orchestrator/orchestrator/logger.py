import os
import sys
import logging
from logging.handlers import RotatingFileHandler


formatter = logging.Formatter("%(filename)s %(asctime)s %(levelname)s %(message)s")
stdout_handler = logging.StreamHandler(stream=sys.stdout)
stdout_handler.setFormatter(formatter)


def get_logger(settings, name=__name__):
    print(f'logger name: {name}')
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        logging.critical(f'YES {logger}')
        return logger

    logging.critical(f'NO {logger}')

    logger.addHandler(stdout_handler)

    if settings.DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if settings.LOGGER_WRITE_IN_FILE:
        log_directory = os.path.join('orchestrator', settings.LOGGER_LOG_FILES_PATH)

        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        log_file_path = os.path.join(log_directory, f"orchestrator.log")
        file_handler = RotatingFileHandler(filename=log_file_path, mode='w', maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
