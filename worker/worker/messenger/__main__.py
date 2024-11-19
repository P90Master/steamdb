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
    logger = get_logger(settings, name='messenger')

    task_manager = TaskManager(
        messenger_channel=orchestrator_channel,
        backend_api_client=backend_api_client,
        steam_api_client=steam_api_client
    )

    def handle_income_task(ch, method, properties, body):
        task_manager.handle_received_task_message(ch, method, properties, body)

    orchestrator_channel.basic_consume(queue=settings.RABBITMQ_INCOME_QUERY, on_message_callback=handle_income_task)

    def async_heartbeats():
        def process_events():
            while True:
                orchestrator_channel.connection.process_data_events()
                time.sleep(5)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_events())

    heartbeat_thread = threading.Thread(target=async_heartbeats)
    heartbeat_thread.start()

    while True:
        try:
            orchestrator_channel.start_consuming()
            orchestrator_channel.connection.process_data_events()

        except HandledException:
            continue

        except AMQPConnectionError:
            time.sleep(1)

        except Exception as unhandled_critical_error:
            logger.critical(f"An unhandled exception received. Exception: {unhandled_critical_error}")
            break

    heartbeat_thread.join()


if __name__ == '__main__':
    main()
