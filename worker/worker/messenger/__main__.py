import asyncio
import time
import threading

from pika.exceptions import AMQPConnectionError

from worker.config import settings
from worker.logger import get_logger
from worker.api import backend_api_client, steam_api_client

from .connections import orchestrator_channel
from .tasks import TaskManager
from .utils import HandledException


def main():
    common_logger = get_logger(settings, name='worker')
    task_logger = get_logger(settings, name='orchestrator_task')

    task_manager = TaskManager(
        messenger_channel=orchestrator_channel,
        backend_api_client=backend_api_client,
        steam_api_client=steam_api_client,
        logger=task_logger
    )

    def handle_income_task(ch, method, properties, body):
        task_manager.handle_received_task_message(ch, method, properties, body)

    orchestrator_channel.basic_consume(queue=settings.RABBITMQ_INCOME_QUERY, on_message_callback=handle_income_task)

    def async_heartbeats(stop_consuming_messages_):
        def process_events(stop_event):
            while not stop_event.is_set():
                time.sleep(settings.RABBITMQ_HEARTBEATS_TIMEOUT)
                orchestrator_channel.connection.process_data_events()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_events(stop_consuming_messages_))

    stop_consuming_messages = threading.Event()
    heartbeat_thread = threading.Thread(target=async_heartbeats, args=(stop_consuming_messages,))
    heartbeat_thread.start()

    while True:
        try:
            orchestrator_channel.start_consuming()

        except HandledException:
            orchestrator_channel.stop_consuming()

        except AMQPConnectionError:
            orchestrator_channel.stop_consuming()
            common_logger.error("Lost connection with Orchestrator<->Workers message broker. ")
            # TODO: try to reconnect (up to N times, then raise critical error)
            time.sleep(2)

        except Exception as unhandled_critical_error:
            common_logger.critical(f"An unhandled exception received. Exception: {unhandled_critical_error}")
            stop_consuming_messages.set()
            orchestrator_channel.stop_consuming()
            break

    heartbeat_thread.join()


if __name__ == '__main__':
    main()
