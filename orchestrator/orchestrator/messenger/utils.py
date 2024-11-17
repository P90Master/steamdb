import asyncio
import functools


class HandledException(Exception):
    pass


def batch_slicer(collection, batch_size=1000):
    for i in range(0, len(collection), batch_size):
        yield collection[i:i + batch_size]


def trace_logs(decorated):
    @functools.wraps(decorated)
    def sync_wrapper(self, *args, **kwargs):
        task_name = decorated.__name__
        if not hasattr(self, 'logger'):
            raise AttributeError(f"Decorated method {task_name} doesn't have logger")

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

    async def async_wrapper(self, *args, **kwargs):
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
