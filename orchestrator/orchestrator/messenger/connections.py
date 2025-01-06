import pika

from orchestrator.core.config import settings


def create_channel() -> tuple[pika.adapters.blocking_connection.BlockingChannel, pika.BlockingConnection]:
    new_connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            connection_attempts=settings.RABBITMQ_CONNECTION_ATTEMPTS,
            retry_delay=settings.RABBITMQ_CONNECTION_RETRY_DELAY,
            heartbeat=settings.RABBITMQ_HEARTBEATS_MAX_DELAY,
            port=settings.RABBITMQ_PORT,
            credentials=pika.PlainCredentials(
                username=settings.RABBITMQ_USER,
                password=settings.RABBITMQ_PASSWORD
            )
        )
    )

    new_channel = new_connection.channel()
    channel_args = {'x-max-priority': 5}
    new_channel.queue_declare(queue=settings.RABBITMQ_INCOME_QUERY, durable=True, arguments=channel_args)
    new_channel.queue_declare(queue=settings.RABBITMQ_OUTCOME_QUERY, durable=True, arguments=channel_args)
    new_channel.basic_qos(prefetch_count=1)
    return new_channel, new_connection
