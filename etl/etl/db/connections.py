from pymongo import MongoClient
from pymongo.collection import Collection

from etl.utils import backoff
from etl.core.logger import get_logger
from etl.core.config import settings


logger = get_logger(settings, 'db')


@backoff(start_sleep_time=5, max_sleep_time=60.0, logger=None)
def connect_to_db(url: str, db_name: str, collection_name: str) -> Collection:
    mongo_client = MongoClient(url)
    mongo_db = mongo_client[db_name]
    mongo_collection = mongo_db[collection_name]
    return mongo_collection
