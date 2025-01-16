import abc
import time
from typing import Any

from etl.core.config import settings
from etl.core.logger import get_logger
from etl.state_storage import StateStorage


class AbstractQueue:
    @abc.abstractmethod
    def get(self) -> Any:
        ...

    @abc.abstractmethod
    def get_batch(self, amount: int = 1, wait_full: bool = False, timeout: int = 5) -> list[Any]:
        ...

    @abc.abstractmethod
    def put(self, items: Any):
        ...


class PipelineComponent:

    logger = get_logger(settings, 'pipeline')

    def __init__(
            self,
            state_storage: StateStorage,
            input_queue: AbstractQueue | None = None,
            output_queue: AbstractQueue | None = None,
            *args,
            **kwargs
    ):
        self.state_storage: StateStorage = state_storage
        self.input_queue: AbstractQueue = input_queue
        self.output_queue: AbstractQueue = output_queue

    def __call__(self, *args, **kwargs):
        self.stop()
        time.sleep(65)  # Ensure that if there are parallel processes, they will read new status and stop
        self.start()

    def start(self):
        if self.state_storage.is_running:
            self.logger.warning(f'{self.__class__.__name__} already started, stop it before run')
            return

        else:
            self.state_storage.set_running_status()
            self.logger.info(f'{self.__class__.__name__} started')

        # logic here

    def stop(self):
        self.state_storage.set_stopped_status()
        self.logger.info(f'{self.__class__.__name__} stopped')
