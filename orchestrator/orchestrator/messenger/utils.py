import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor


THREAD_POOL_EXECUTOR_MAX_WORKERS = 5


class HandledException(Exception):
    pass


def batch_slicer(collection, batch_size=1000):
    for i in range(0, len(collection), batch_size):
        yield collection[i:i + batch_size]


# FIXME: Dead code
def async_execute(coro: callable) -> callable:
    def run_coro(coroutine: callable, *args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(coroutine(*args, **kwargs))
        loop.close()
        return result

    @functools.wraps(coro)
    def wrapper(*args, **kwargs):
        with ThreadPoolExecutor(max_workers=THREAD_POOL_EXECUTOR_MAX_WORKERS) as executor:
            return executor.submit(run_coro, coro, *args, **kwargs).result()

    return wrapper


def trace_logs(decorated: callable):
    @functools.wraps(decorated)
    def sync_wrapper(self: object, *args, **kwargs):
        task_name = decorated.__name__
        if not hasattr(self, 'logger'):
            raise AttributeError(f"Class of decorated method {task_name} doesn't have logger")

        self.logger.info(f"Received command to execute task: {task_name}")

        try:
            result = decorated(self, *args, **kwargs)

        except HandledException as handled_exception:
            raise handled_exception

        except Exception as error:
            error_message = f'Task "{task_name}" execution failed with error: {error}'
            self.logger.error(error_message)
            raise HandledException(error_message)

        else:
            self.logger.info(f"Task executed: {task_name}")
            return result

    async def async_wrapper(self: object, *args, **kwargs):
        task_name = decorated.__name__
        if not hasattr(self, 'logger'):
            raise AttributeError(f"Decorated method {task_name} doesn't have logger")

        self.logger.info(f"Received command to execute task: {task_name}")

        try:
            result = await decorated(self, *args, **kwargs)

        except HandledException as handled_exception:
            raise handled_exception

        except Exception as error:
            error_message = f'Task "{task_name}" execution failed with error: {error}'
            self.logger.error(error_message)
            raise HandledException(error_message)

        else:
            self.logger.info(f"Task executed: {task_name}")
            return result

    return async_wrapper if asyncio.iscoroutinefunction(decorated) else sync_wrapper
