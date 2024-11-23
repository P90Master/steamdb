import threading
import time

from pika.exceptions import AMQPConnectionError

from orchestrator.config import settings
from orchestrator.logger import get_logger
from orchestrator.db import Session
from .connections import worker_channel
from .tasks import TaskManager
from .utils import HandledException


def consume_messages():
    logger = get_logger(settings, name='consume_task')

    task_manager = TaskManager(
        messenger_channel=worker_channel,
        session_maker=Session,
        logger=logger
    )

    def handle_income_task(ch, method, properties, body):
        # threading.Thread(target=task_manager.handle_received_task_message, args=(ch, method, properties, body)).start()
        task_manager.handle_received_task_message(ch, method, properties, body)

    worker_channel.basic_consume(queue=settings.RABBITMQ_INCOME_QUERY, on_message_callback=handle_income_task)

    # TODO: run task in new thread & control it amount (semaphore?)
    def process_events(stop_consuming_messages_):
        while not stop_consuming_messages_.is_set():
            worker_channel.connection.process_data_events()
            time.sleep(settings.RABBITMQ_HEARTBEATS_TIMEOUT)

    stop_consuming_messages = threading.Event()
    heartbeat_thread = threading.Thread(target=process_events, args=(stop_consuming_messages,))
    heartbeat_thread.start()

    while True:
        try:
            worker_channel.start_consuming()

        except HandledException:
            pass

        except AMQPConnectionError:
            time.sleep(1)

        except Exception as unhandled_critical_error:
            logger.critical(f"An unhandled exception received. Exception: {unhandled_critical_error}")
            break

    stop_consuming_messages.set()


if __name__ == '__main__':
    consume_messages()
