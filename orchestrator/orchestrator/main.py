import logging
import time

import pika


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='orchestrator-worker-broker',
            port=5672,
            credentials=pika.PlainCredentials('user', 'password')
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue='hello')

    while True:
        channel.basic_publish(exchange='', routing_key='hello', body='Hello World!')
        logging.error("Send to worker command to execute some task")
        time.sleep(30)

    connection.close()


if __name__ == '__main__':
    main()
