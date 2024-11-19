import threading
import time

import pika
from pika.exceptions import AMQPConnectionError

from orchestrator.config import settings
from orchestrator.logger import get_logger
from orchestrator.db import Session
from .connections import worker_channel
from .tasks import TaskManager
from .utils import HandledException


# FIXME: mock celery scheduled tasks & commands from API
def send_messages():
    logger = get_logger(settings, name='messenger')

    worker_connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        )
    )
    channel = worker_connection.channel()
    channel.queue_declare(queue=settings.RABBITMQ_OUTCOME_QUERY, durable=True)
    channel.basic_qos(prefetch_count=1)

    task_manager = TaskManager(channel, Session)

    def process_events():
        while True:
            worker_connection.process_data_events()
            time.sleep(1)

    event_thread = threading.Thread(target=process_events, daemon=True)
    event_thread.start()

    while True:
        try:
            task_manager.request_all_apps()
            time.sleep(120)
            task_manager.bulk_request_for_apps_data()
            time.sleep(300)

        except AMQPConnectionError:
            time.sleep(1)

        except Exception as error:
            logger.critical(f'Unhandled error: {error}')
            return

def consume_messages():
    logger = get_logger(settings, name='messenger')

    task_manager = TaskManager(
        messenger_channel=worker_channel,
        session_maker=Session
    )

    def handle_income_task(ch, method, properties, body):
        # threading.Thread(target=task_manager.handle_received_task_message, args=(ch, method, properties, body)).start()
        task_manager.handle_received_task_message(ch, method, properties, body)

    worker_channel.basic_consume(queue=settings.RABBITMQ_INCOME_QUERY, on_message_callback=handle_income_task)

    while True:
        try:
            worker_channel.start_consuming()
            worker_channel.connection.process_data_events()

        except HandledException:
            pass

        except AMQPConnectionError:
            time.sleep(1)

        except Exception as unhandled_critical_error:
            logger.critical(f"An unhandled exception received. Exception: {unhandled_critical_error}")
            return


def main():
    send_thread = threading.Thread(target=send_messages, name='sending tasks')
    consume_thread = threading.Thread(target=consume_messages, name='handling worker response')

    consume_thread.start()
    send_thread.start()

    send_thread.join()
    consume_thread.join()


if __name__ == '__main__':
    main()
