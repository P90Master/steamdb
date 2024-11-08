import asyncio
import json

from worker.connections import orchestrator_connection
from worker.logger import logger
from worker.tasks import worker_tasks_registry


def callback(ch, method, properties, body):
    logger.debug(f"Received message from orchestrator {body}")
    data = json.loads(body)

    if not (requested_task_name := data.get('task')):
        # TODO: id of message & logging it (broker deletes messages - save wrong messages for debug?)
        logger.error(f"Message received from the orchestrator doesn't contain the task name. Message discarded.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    if not (worker_task := worker_tasks_registry.get(requested_task_name)):
        logger.error(f'Message received from the orchestrator contains an invalid task name '
                     f'- a task named "{requested_task_name}" does not exist. Message discarded.')
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(worker_task(**data.get('params', {})))

    except TypeError:
        logger.error(f'The parameters passed to the task "{requested_task_name}" do not match its signature')

    except Exception as unhandled:
        raise unhandled

    else:
        logger.debug(f'Message containing the request to perform task "{requested_task_name}"'
                     f' was processed successfully.'
                     f' Result: {result}')

    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


orchestrator_channel = orchestrator_connection.channel()
orchestrator_channel.queue_declare(queue='hello-1', durable=True)
orchestrator_channel.basic_qos(prefetch_count=1)
orchestrator_channel.basic_consume(queue='hello-1', on_message_callback=callback)
