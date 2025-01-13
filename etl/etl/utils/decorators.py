import logging
import functools
import random
import time


def coroutine(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        fn = func(*args, **kwargs)
        next(fn)
        return fn

    return wrapper


def calc_sleep_time(
        start_sleep_time: float, max_sleep_time: float, factor: float, attempt: int, jitter: bool) -> float:
    try:
        sleep_time = (
            random.uniform(start_sleep_time, start_sleep_time * factor) * factor ** attempt
            if jitter else start_sleep_time * factor ** attempt
        )

    except OverflowError:
        sleep_time = max_sleep_time

    return min(max_sleep_time, sleep_time)


def backoff(
        start_sleep_time: float = 5,
        max_sleep_time: float = 30.0,
        factor: float = 2.0,
        jitter: bool = True,
        logger: logging.Logger | None = None
):
    def decorator(func: callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0

            while True:
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    sleep_time = calc_sleep_time(start_sleep_time, max_sleep_time, factor, attempt, jitter)
                    attempt += 1

                    if logger:
                        logger.error(
                            f'Received exception: {e}'
                            f' Attempt: {attempt}'
                            f' Timeout until next attempt: {sleep_time} seconds'
                        )

                    time.sleep(sleep_time)

        return wrapper

    return decorator
