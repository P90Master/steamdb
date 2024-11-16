import pika

from worker.config import settings


# TODO: credentials from ettings
orchestrator_connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='orchestrator-worker-broker',
        port=5672,
        credentials=pika.PlainCredentials('user', 'password')
    )
)

orchestrator_channel = orchestrator_connection.channel()
orchestrator_channel.queue_declare(queue='hello-1', durable=True)
orchestrator_channel.queue_declare(queue='bye-1', durable=True)
orchestrator_channel.basic_qos(prefetch_count=1)
