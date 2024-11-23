import asyncio
import functools
import json
from collections.abc import Iterable
from datetime import datetime

import pika
from sqlalchemy import select, insert, update

from orchestrator.config import settings
from orchestrator.logger import get_logger
from orchestrator.db import App

from .utils import trace_logs, HandledException, batch_slicer


class TaskManagerMeta(type):
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        new_class._receive_tasks = {}

        for attr_name, attr_value in attrs.items():
            if callable(attr_value) and attr_name.startswith('receive_task__'):
                task_name =  attr_name[attr_name.rfind("__") + 2:]
                new_class._receive_tasks[task_name] = attr_value

        return new_class


class TaskManager(metaclass=TaskManagerMeta):
    def __init__(self, messenger_channel, session_maker, logger=None):
        self.messenger_channel = messenger_channel
        self.db_session_maker = session_maker
        self.logger = logger if logger else get_logger(settings, __name__)

    def execute_task(self, task):
        @functools.wraps(task)
        def wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(task(self, **kwargs))

        return wrapper

    def get_receive_task_handler(self, task_name):
        return self._receive_tasks.get(task_name)

    def register_task(self, task_context):
        context_json_payload = json.dumps(task_context)
        self.messenger_channel.basic_publish(
            exchange='',
            routing_key=settings.RABBITMQ_OUTCOME_QUERY,
            body=context_json_payload,
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )

    def handle_received_task_message(self, ch, method, properties, body):
        data = json.loads(body)

        if not (requested_task_name := data.get('task_name')):
            # TODO: id of message & logging it (broker deletes messages - save wrong messages for debug?)
            self.logger.error('Message received from worker doesnt contain "task_name". Message discarded.')
            ch.basic_reject(delivery_tag=method.delivery_tag)
            return

        if not (handle_received_task := self.get_receive_task_handler(requested_task_name)):
            self.logger.error(f'Message received from worker contains an invalid task name '
                              f'- a task named "{requested_task_name}" does not exist. Message discarded.')
            ch.basic_reject(delivery_tag=method.delivery_tag)
            return

        try:
            task_params = data.get('params', {})
            handle_received_task(self, ch, method, properties, task_params)

        except TypeError:
            error_msg = f'The parameters passed to the task "{requested_task_name}" do not match its signature'
            self.logger.error(error_msg)
            ch.basic_reject(delivery_tag=method.delivery_tag)

        except HandledException as handled_exception:
            ch.basic_reject(delivery_tag=method.delivery_tag)

        except Exception as unhandled_error:
            error_msg = f'Task "{requested_task_name}" execution failed with error: {unhandled_error}'
            self.logger.error(error_msg)
            ch.basic_reject(delivery_tag=method.delivery_tag)

        else:
            self.logger.debug(
                f'Message containing the request to perform task "{requested_task_name}"'
                f' was processed successfully.'
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

    @trace_logs
    def request_apps_list(self):
        # TODO: Worker tasks registry
        task_context = {
            "task_name": "request_apps_list",
            "params": {}
        }
        self.register_task(task_context)

    @trace_logs
    def request_app_data(self, app_id: str, country_code: str):
        task_context = {
            "task_name": "request_app_data",
            "params": {
                "app_id": app_id,
                "country_code": country_code
            }
        }
        self.register_task(task_context)

    @trace_logs
    def bulk_request_for_apps_data(
            self,
            batch_size=settings.BATCH_SIZE_OF_UPDATING_STEAM_APPS,
            country_codes=settings.DEFAULT_COUNTRY_BUNDLE
    ):
        def get_apps_need_updating() -> Iterable[int]:
            query = (
                select(App.id)
                .order_by(App.last_updated)
                .limit(batch_size)
            )

            with self.db_session_maker() as session:
                return list(session.execute(query).scalars().all())

        app_ids = get_apps_need_updating()

        task_context = {
            "task_name": "bulk_request_for_apps_data",
            "params": {
                "app_ids": app_ids,
                "country_codes": country_codes
            }
        }
        self.register_task(task_context)


    @trace_logs
    def receive_task__actualize_app_list(self, ch, method, properties, task_params):
        if not (app_ids := task_params.get('app_ids')):
            error_msg = 'Task "actualize_app_list": No app_ids provided in task context'
            self.logger.error(error_msg)
            raise HandledException(error_msg)

        actual_ids = set(app_ids)

        existing_ids_query = select(App.id)
        # TODO: Async insert
        with self.db_session_maker() as session:
            existing_ids = {row[0] for row in session.execute(existing_ids_query)}
            new_ids = list(actual_ids - existing_ids)
            self.logger.debug(f'Task "actualize_app_list": received {len(new_ids)} new apps')

            for batch_of_ids in batch_slicer(new_ids, settings.DB_INPUT_BATCH_SIZE):
                query = insert(App).values(
                    [{"id": app_id, "last_updated": datetime.fromtimestamp(0)} for app_id in batch_of_ids]
                )
                session.execute(query)
                session.commit()

    @trace_logs
    def receive_task__update_apps_status(self, ch, method, properties, task_params):
        if not (app_ids := task_params.get('app_ids')):
            error_msg = 'Task "update_apps_status": No app_ids provided in task context'
            self.logger.error(error_msg)
            raise HandledException(error_msg)

        # TODO: Async update
        with self.db_session_maker() as session:
            for batch_of_ids in batch_slicer(app_ids, settings.DB_INPUT_BATCH_SIZE):
                query = (
                    update(App)
                    .where(App.id.in_(batch_of_ids))
                    .values(last_updated=datetime.now())
                )

                session.execute(query)
                session.commit()
