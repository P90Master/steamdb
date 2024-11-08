import json
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
    channel.queue_declare(queue='hello-1', durable=True)

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

    connection.close()


if __name__ == '__main__':
    main()
