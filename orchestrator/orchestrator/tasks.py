import functools
import json

import pika


class TaskManager:
    def __init__(self, messenger_channel, db, logger):
        self.messenger_channel = messenger_channel
        self.db = db
        self.logger = logger

        self._send_tasks = {}
        self._receive_tasks = {}

    @staticmethod
    def task_name(task_name):
        def decorator(decorated):
            @functools.wraps(decorated)
            def wrapper(*args, **kwargs):
                return decorated(*args, **kwargs)

            wrapper.__name__ = task_name
            return wrapper

        return decorator

    def trace_logs(self, decorated):
        @functools.wraps(decorated)
        def wrapper(*args, **kwargs):
            task_name_ = decorated.__name__
            self.logger.info(f"Received command to register task: {task_name_}")
            result = decorated(*args, **kwargs)
            self.logger.info(f"Task registered: {task_name_}")
            return result

        return wrapper

    def receive(self, decorated):
        @functools.wraps(decorated)
        def wrapper(*args, **kwargs):
            self._receive_tasks[decorated.__name__] = decorated
            return decorated(*args, **kwargs)

        return wrapper

    def send(self, decorated):
        @functools.wraps(decorated)
        def wrapper(*args, **kwargs):
            self._send_tasks[decorated.__name__] = decorated
            return decorated(*args, **kwargs)

        return wrapper

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

    def handle_received_task_result(self, ch, method, properties, body):
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
            result = handle_received_task(self, ch, method, properties, body)

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
    @send
    @task_name("request_all_apps")
    def request_for_actual_app_list(self):
        worker_task_data = {
            "task": "request_all_apps",
            "params": {}
        }
        self._send_message(worker_task_data)

    @trace_logs
    @send
    def request_for_app_data(self, app_id: str, country_code: str):
        pass

    @trace_logs
    @send
    def bulk_request_for_apps_data(self, app_id: str, country_code: str):
        pass

    @trace_logs
    @receive
    def update_app_list(self, ch, method, properties, body):
        pass