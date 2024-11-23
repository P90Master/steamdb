import pika

from orchestrator.config import settings


worker_connection = pika.BlockingConnection(
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

worker_channel = worker_connection.channel()
worker_channel.queue_declare(queue=settings.RABBITMQ_INCOME_QUERY, durable=True)
worker_channel.queue_declare(queue=settings.RABBITMQ_OUTCOME_QUERY, durable=True)
worker_channel.basic_qos(prefetch_count=1)
