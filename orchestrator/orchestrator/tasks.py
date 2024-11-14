import functools
import json

import pika
from sqlalchemy import select, insert

from orchestrator.db.models import App


def trace_logs(decorated):
    @functools.wraps(decorated)
    def wrapper(self, *args, **kwargs):
        task_name = decorated.__name__
        if not hasattr(self, 'logger'):
            raise AttributeError(f"Decorated method {task_name} doesn't have logger")

        self.logger.info(f"Received command to execute task: {task_name}")

        try:
            result = decorated(self, *args, **kwargs)

        # TODO: special exception for failed task with handled error as signal for upper handlers
        except Exception as error:
            self.logger.error(f'Task "{task_name}" execution failed with error: {error}')

        else:
            self.logger.info(f"Task executed: {task_name}")
            return result

    return wrapper


class TaskManagerMeta(type):
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        new_class._receive_tasks = {}

        for attr_name, attr_value in attrs.items():
            if callable(attr_value) and attr_name.startswith('receive__'):
                task_name =  attr_name[attr_name.rfind("__") + 2:]
                new_class._receive_tasks[task_name] = attr_value

        return new_class

# FIXME: outdated
class TaskManager(metaclass=TaskManagerMeta):
    def __init__(self, messenger_channel, session_maker, logger):
        self.messenger_channel = messenger_channel
        self.db_session_maker = session_maker
        self.logger = logger

    def get_receive_task_handler(self, task_name):
        return self._receive_tasks.get(task_name)

    def _send_message(self, data):
        data_json_payload = json.dumps(data)
        self.messenger_channel.basic_publish(
            exchange='',
            routing_key='hello-1',
            body=data_json_payload,
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )

    def handle_received_task_message(self, ch, method, properties, body):
        data = json.loads(body)
        if not (requested_task_name := data.get('task')):
            # TODO: id of message & logging it (broker deletes messages - save wrong messages for debug?)
            self.logger.error(f"Message received from worker doesn't contain the task name. Message discarded.")
            ch.basic_reject(delivery_tag=method.delivery_tag)
            return

        if not (handle_received_task := self.get_receive_task_handler(requested_task_name)):
            self.logger.error(f'Message received from orchestrator contains an invalid task name '
                         f'- a task named "{requested_task_name}" does not exist. Message discarded.')
            ch.basic_reject(delivery_tag=method.delivery_tag)
            return

        try:
            result = handle_received_task(self, ch, method, properties, data)

        except TypeError:
            self.logger.error(f'The parameters passed to the task "{requested_task_name}" do not match its signature')
            ch.basic_reject(delivery_tag=method.delivery_tag)

        except Exception as unhandled:
            ch.basic_reject(delivery_tag=method.delivery_tag)
            raise unhandled

        else:
            self.logger.debug(f'Message containing the request to perform task "{requested_task_name}"'
                         f' was processed successfully.'
                         f' Result: {result}')
            ch.basic_ack(delivery_tag=method.delivery_tag)

    @trace_logs
    def request_all_apps(self):
        worker_task_data = {
            "task": "request_all_apps",
            "params": {}
        }
        self._send_message(worker_task_data)

    @trace_logs
    def request_for_app_data(self, app_id: str, country_code: str):
        pass

    @trace_logs
    def bulk_request_for_apps_data(self, app_id: str, country_code: str):
        pass

    @trace_logs
    def receive__update_app_list(self, ch, method, properties, data):
        if not (app_ids := data.get('task_result')):
            self.logger.error(f'Task "{__name__}" received empty app ids list.')
            return

        actual_ids = set(app_ids)

        existing_ids_query = select(App.c.id)
        with self.db_session_maker() as session:
            existing_ids = {row[0] for row in session.execute(existing_ids_query)}
            new_ids = actual_ids - existing_ids

            if new_ids:
                stmt = insert(App).values([{"id": app_id} for app_id in new_ids])
                session.execute(stmt)

    @trace_logs
    def receive__update_apps_status(self, ch, method, properties, data):
        raise NotImplemented
