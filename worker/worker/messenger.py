from worker.connections import orchestrator_connection
from worker.logger import logger


def callback(ch, method, properties, body):
    logger.info(f"Received message from orchestrator {body}")


orchestrator_channel = orchestrator_connection.channel()
orchestrator_channel.queue_declare(queue='hello')
orchestrator_channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)
