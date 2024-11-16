import pika

from worker.config import settings


orchestrator_connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        credentials=pika.PlainCredentials(
            username=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASSWORD
        )
    )
)

orchestrator_channel = orchestrator_connection.channel()
orchestrator_channel.queue_declare(queue=settings.RABBITMQ_INCOME_QUERY, durable=True)
orchestrator_channel.queue_declare(queue=settings.RABBITMQ_OUTCOME_QUERY, durable=True)
orchestrator_channel.basic_qos(prefetch_count=1)
