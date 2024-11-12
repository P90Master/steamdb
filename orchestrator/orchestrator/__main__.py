import pika
import threading
import time

from orchestrator.config import settings
from orchestrator.tasks import TaskManager
from orchestrator.db.connection import Session
from logger import logger


def build_messenger_connection(settings):
    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        )
    )

def send_messages():
    worker_connection = build_messenger_connection(settings)
    channel = worker_connection.channel()
    channel.queue_declare(queue='hello-1', durable=True)
    channel.basic_qos(prefetch_count=1)

    task_manager = TaskManager(channel, Session, logger)

    try:
        while True:
            task_manager.request_for_actual_app_list()
            time.sleep(120)

    except Exception as error:
        logger.critical(f'Unhandled error: {error}')
        worker_connection.close()


def consume_messages():
    def handle_message(ch, method, properties, body):
        task_manager.handle_received_task_message(ch, method, properties, body)

    worker_connection = build_messenger_connection(settings)
    channel = worker_connection.channel()
    channel.queue_declare(queue='bye-1', durable=True)
    channel.basic_qos(prefetch_count=1)
    task_manager = TaskManager(channel, Session, logger)
    channel.basic_consume(queue='bye-1', on_message_callback=handle_message)
    channel.start_consuming()


def main():
    send_thread = threading.Thread(target=send_messages, name='sending tasks')
    consume_thread = threading.Thread(target=consume_messages, name='handling worker response')

    consume_thread.start()
    send_thread.start()

    send_thread.join()
    consume_thread.join()


if __name__ == '__main__':
    main()
