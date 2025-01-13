import random
import time


def random_sleep(min_sleep_time: float = 1.0, max_sleep_time: float = 30.0):
    time_ = random.uniform(min_sleep_time, max_sleep_time)
    time.sleep(time_)
