import asyncio
import functools
import json
from typing import Sized

import pika

from worker.config import settings
from worker.utils import convert_steam_app_data_response_to_backend_app_data_package, trace_logs, HandledException
from worker.logger import logger
from worker.celery import execute_celery_task, get_app_list_celery_task, get_app_detail_celery_task


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
    def __init__(self, messenger_channel, backend_api_client, steam_api_client, logger):
        self.messenger_channel = messenger_channel
        self.backend_api_client = backend_api_client
        self.steam_api_client = steam_api_client
        self.logger = logger

    def execute_task(self, task):
        @functools.wraps(task)
        def wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(task(self, **kwargs))

        return wrapper

    def get_receive_task_handler(self, task_name):
        return self._receive_tasks.get(task_name)

    def _register_task(self, data):
        data_json_payload = json.dumps(data)
        self.messenger_channel.basic_publish(
            exchange='',
            # FIXME: queues
            routing_key='bye-1',
            body=data_json_payload,
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )

    def handle_received_task_message(self, ch, method, properties, body):
        data = json.loads(body)

        if not (requested_task_name := data.get('task')):
            # TODO: id of message & logging it (broker deletes messages - save wrong messages for debug?)
            self.logger.error(f"Message received from orchestrator doesn't contain the task name. Message discarded.")
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
    def receive_task__request_apps_list(self, ch, method, properties, body):
        result = self.execute_task(self._request_apps_list_task)
        orchestrator_task_context = {
            "task_name": "update_app_list",
            "params": {
                "app_ids": result
            }
        }
        self._register_task(orchestrator_task_context)

    async def _request_apps_list_task(self):
        logger.info('Requesting apps list..')

        apps_collection, is_success = await execute_celery_task(celery_task=get_app_list_celery_task)
        if not is_success:
            logger.error("Requesting apps list failed")
            return

        app_list = [app.get('appid') for app in apps_collection.get('applist', {}).get('apps', {})]
        logger.info('Apps list successfully requested')
        return app_list


# FIXME: code below is outdated ##############################################################

    @trace_logs
    def receive_task__request_app_data(self, ch, method, properties, body):
        result = self.execute_task(self._request_app_data_task)(ch, method, properties, body)
        orchestrator_task_context = {
            "task_name": "update_app_list",
            "params": {
                "app_ids": result
            }
        }
        self._register_task(orchestrator_task_context)

    @trace_logs
    async def _request_app_data_task(self, app_id: str, country_code: str = settings.DEFAULT_COUNTRY_CODE):
        logger.info(f'Requesting app data. AppID: {app_id} CountryCode: {country_code}')

        request_params = {
            'app_id': app_id,
            'country_code': country_code
        }

        app_data_response, is_success = await execute_celery_task(celery_task=get_app_detail_celery_task,
                                                                  **request_params)
        if not is_success:
            logger.error(f"Requesting app data failed. AppID: {app_id} CountryCode: {country_code}")
            return

        logger.info(f'App data requested successfully. AppID: {app_id} CountryCode: {country_code}')

        backend_package = convert_steam_app_data_response_to_backend_app_data_package(request_params, app_data_response)

        try:
            await self.backend_api_client.post_app_data_package(backend_package)

        except Exception as error:
            logger.error(
                f"Receive an error while requesting app data."
                f" App ID: {app_id} CountryCode: {country_code}"
                f" Error: {error}"
            )

        else:
            logger.info(f'App data successfully pushed to backend. AppID: {app_id} CountryCode: {country_code}')
            return {
                "updated_app_ids": [app_id],
                "country_code": country_code
            }

    @trace_logs
    async def receive_task__request_batch_of_apps_data(
            self,
            batch_of_app_ids: Sized,
            country_code: str = settings.DEFAULT_COUNTRY_CODE
    ):
        # TODO: wrap steam requests in celery task

        logger.info(
            f'Requesting batch of apps data.'
            f' Batch of app IDs size: {len(batch_of_app_ids)} CountryCode: {country_code}'
        )

        backend_request_tasks = set()
        successfully_updated_app_ids = set()

        def save_successfully_updated_app_id_and_clear_task_pool(backend_task):
            # TODO: if task has exception (because of it asyncio.wait stopped and this in done) ?
            backend_request_tasks.discard(backend_task)
            updated_app_id = (backend_task.result() or {}).get('data', {}).get('id')
            if updated_app_id:
                successfully_updated_app_ids.add(updated_app_id)

        async with self.backend_api_client as backend_session:
            for app_id in batch_of_app_ids:
                request_params = {
                    'app_id': app_id,
                    'country_code': country_code
                }

                app_data_response, is_success = await execute_celery_task(
                    celery_task=get_app_detail_celery_task,
                    **request_params
                )
                if not is_success:
                    logger.error(f"Requesting app data failed. AppID: {app_id} CountryCode: {country_code}")
                    continue

                backend_package = convert_steam_app_data_response_to_backend_app_data_package(
                    request_params,
                    app_data_response
                )

                task = asyncio.create_task(backend_session.post_app_data_package(backend_package))
                backend_request_tasks.add(task)
                task.add_done_callback(save_successfully_updated_app_id_and_clear_task_pool)

            done, pending = await asyncio.wait(backend_request_tasks, return_when=asyncio.FIRST_EXCEPTION)

            if exc := done.pop().exception():
                for task in pending:
                    task.cancel()

                logger.error(
                    f"Receive an error while requesting batch of apps data."
                    f" Batch of app IDs size: {len(batch_of_app_ids)} CountryCode: {country_code}"
                    f" Error: {exc}"
                    f" Amount of canceled tasks (except task with error): {len(pending)}"
                )

            return {
                "updated_app_ids": list(successfully_updated_app_ids),
                "country_code": country_code
            }
