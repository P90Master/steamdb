import time
import threading

from pika.exceptions import AMQPConnectionError, ChannelWrongStateError
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties, Basic

from worker.core.config import settings
from worker.core.logger import get_logger
from worker.api import backend_api_client, steam_api_client

from .connections import create_channel
from .tasks import TaskManager
from .utils import HandledException, HandledCriticalException


def consume_messages():
    task_logger = get_logger(settings, name='messenger.received_orchestrator_task')
    base_logger = get_logger(settings, name='messenger')
    orchestrator_channel, broker_connection = create_channel()

    task_manager = TaskManager(
        messenger_channel=orchestrator_channel,
        backend_api_client=backend_api_client,
        steam_api_client=steam_api_client,
        logger=task_logger
    )

    def handle_income_task(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes):
        task_manager.handle_received_task_message(ch, method, properties, body)

    orchestrator_channel.basic_consume(queue=settings.RABBITMQ_INCOME_QUERY, on_message_callback=handle_income_task)

    def process_events(stop_event: threading.Event):
        while not stop_event.is_set():
            time.sleep(settings.RABBITMQ_HEARTBEATS_TIMEOUT)
            orchestrator_channel.connection.process_data_events()

    stop_consuming_messages = threading.Event()
    heartbeat_thread = threading.Thread(target=process_events, args=(stop_consuming_messages,), daemon=True)
    heartbeat_thread.start()

    while True:
        try:
            orchestrator_channel.start_consuming()

        except HandledException:
            orchestrator_channel.stop_consuming()

        except ChannelWrongStateError:
            base_logger.warning(f"Broker channel closed. Reopening...")
            orchestrator_channel.stop_consuming()
            broker_connection.close()
            orchestrator_channel, broker_connection = create_channel()

        except AMQPConnectionError:
            # TODO: try to reconnect (up to N times, then raise critical error)
            base_logger.warning(f"Connection to broker lost. Reconnecting...")
            orchestrator_channel.stop_consuming()
            broker_connection.close()
            time.sleep(5)
            worker_channel, broker_connection = create_channel()

        except HandledCriticalException as handled_critical_error:
            base_logger.critical(f"Critical exception received. Exception: {handled_critical_error}")
            orchestrator_channel.stop_consuming()
            stop_consuming_messages.set()
            broker_connection.close()
            break

        except Exception as unhandled_critical_error:
            base_logger.critical(f"An unhandled exception received. Exception: {unhandled_critical_error}")
            stop_consuming_messages.set()
            orchestrator_channel.stop_consuming()
            broker_connection.close()
            break


if __name__ == '__main__':
    consume_messages()
