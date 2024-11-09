import json
import logging

import pika
import threading
import time


def send_messages():
    worker_connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='orchestrator-worker-broker',
            port=5672,
            credentials=pika.PlainCredentials('user', 'password')
        )
    )
    channel = worker_connection.channel()
    channel.queue_declare(queue='hello-1', durable=True)
    channel.basic_qos(prefetch_count=1)

    try:
        while True:
            worker_task_data = {
                "task": "batch_update_apps_data",
                "params": {
                    "batch_of_app_ids": [945360, 570, 292030],
                    "country_code": "GB"
                }
            }
            task_data_json_payload = json.dumps(worker_task_data)
            channel.basic_publish(
                exchange='',
                routing_key='hello-1',
                body=task_data_json_payload,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            logging.error("Send to worker command to execute some task")
            time.sleep(40)

    except Exception as error:
        logging.critical(f'Unhandled error: {error}')
        worker_connection.close()


def consume_messages():
    worker_connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='orchestrator-worker-broker',
            port=5672,
            credentials=pika.PlainCredentials('user', 'password')
        )
    )
    channel = worker_connection.channel()
    channel.queue_declare(queue='bye-1', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='bye-1', on_message_callback=handle_task_response)
    channel.start_consuming()


def handle_task_response(ch, method, properties, body):
    logging.error(f"Received message from worker {json.loads(body)}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    send_thread = threading.Thread(target=send_messages, name='sending tasks')
    consume_thread = threading.Thread(target=consume_messages, name='handling worker response')

    consume_thread.start()
    send_thread.start()

    send_thread.join()
    consume_thread.join()


if __name__ == '__main__':
    main()
