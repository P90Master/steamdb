import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from worker.settings import DEBUG


logger_name = "worker" if __name__ == "__main__" else __name__

logger = logging.getLogger(logger_name)

if DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

log_directory = "logs"

if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_file_path = os.path.join(log_directory, f"worker.log")
file_handler = RotatingFileHandler(filename=log_file_path, mode='w', maxBytes=10*1024*1024, backupCount=5)
formatter = logging.Formatter("%(filename)s %(asctime)s %(levelname)s %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stdout_handler = logging.StreamHandler(stream=sys.stdout)
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)
