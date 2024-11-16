import asyncio
import functools
import json

import pika

from worker.config import settings
from worker.celery import execute_celery_task, get_app_list_celery_task, get_app_detail_celery_task
from .utils import convert_steam_app_data_response_to_backend_app_data_package, trace_logs, HandledException


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

    def register_response_task(self, data):
        data_json_payload = json.dumps(data)
        self.messenger_channel.basic_publish(
            exchange='',
            routing_key=settings.RABBITMQ_OUTCOME_QUERY,
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
            handle_received_task(self, ch, method, properties, data)

        except TypeError:
            error_msg = f'The parameters passed to the task "{requested_task_name}" do not match its signature'
            self.logger.error(error_msg)
            ch.basic_reject(delivery_tag=method.delivery_tag)
            raise HandledException(error_msg)

        except HandledException as handled_exception:
            ch.basic_reject(delivery_tag=method.delivery_tag)
            raise handled_exception

        except Exception as unhandled_error:
            error_msg = f'Task "{requested_task_name}" execution failed with error: {unhandled_error}'
            self.logger.error(error_msg)
            ch.basic_reject(delivery_tag=method.delivery_tag)
            raise HandledException(error_msg)

        else:
            self.logger.debug(
                f'Message containing the request to perform task "{requested_task_name}"'
                f' was processed successfully.'
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

    @trace_logs
    def receive_task__request_apps_list(self, ch, method, properties, data):
        async def _task():
            self.logger.info('Requesting apps list..')

            apps_collection, is_success = await execute_celery_task(celery_task=get_app_list_celery_task)
            if not is_success:
                error_msg = "Requesting apps list failed"
                self.logger.error(error_msg)
                raise HandledException(error_msg)

            app_list = [app.get('appid') for app in apps_collection.get('applist', {}).get('apps', {})]
            self.logger.info('Apps list successfully requested')
            return app_list

        result = self.execute_task(_task)
        orchestrator_task_context = {
            # TODO: task names as settings consts
            "task_name": "update_app_list",
            "params": {
                "app_ids": result
            }
        }
        self.register_response_task(orchestrator_task_context)

    @trace_logs
    def receive_task__request_app_data(self, ch, method, properties, data):
        async def _task():
            self.logger.info(f'Requesting app data. AppID: {app_id} CountryCode: {country_code}')

            request_params = {'app_id': app_id, 'country_code': country_code}
            app_data_response, is_success = await execute_celery_task(
                celery_task=get_app_detail_celery_task,
                **request_params
            )
            if not is_success:
                error_message = f"Requesting app data from steam failed. AppID: {app_id} CountryCode: {country_code}"
                self.logger.error(error_message)
                raise HandledException(error_message)

            self.logger.info(f'App data requested successfully. AppID: {app_id} CountryCode: {country_code}')
            backend_package = convert_steam_app_data_response_to_backend_app_data_package(
                request_params,
                app_data_response,
                self.logger
            )
            try:
                await self.backend_api_client.post_app_data_package(backend_package)
                # TODO: Record update time - when request was sent to backend (instead of time.now() on orchestrator)

            except Exception as unhandled_error:
                error_message = (
                    # TODO: 'Task "request_app_data": ' prefix in consts
                    f'Task "request_app_data": Receive an error while requesting app data.'
                    f" App ID: {app_id} CountryCode: {country_code}"
                    f" Error: {unhandled_error}"
                )
                self.logger.error(error_message)
                raise HandledException(error_message)

            self.logger.info(f'App data successfully pushed to backend. AppID: {app_id} CountryCode: {country_code}')
            return {
                "updated_app_ids": [app_id],
                "country_code": country_code
            }

        # main body ###########################

        if not (app_id := data.get('app_id')):
            error_msg = 'Task "request_app_data": No app_id specified in app data request'
            self.logger.error(error_msg)
            raise HandledException(error_msg)

        if not (country_code := data.get('country_code', settings.DEFAULT_COUNTRY_CODE)):
            self.logger.warning(
                f'Task "request_app_data": No country specified for app_id {app_id} data request. '
                f'Default country selected - {country_code}'
            )

        result = self.execute_task(_task)()
        orchestrator_task_context = {
            "task_name": "update_apps_status",
            "params": {
                "app_ids": result
            }
        }
        self.register_response_task(orchestrator_task_context)

    @trace_logs
    def receive_task__request_batch_of_apps_data(self, ch, method, properties, data):
        async def _task():
            self.logger.info(
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
                        self.logger.error(f"Requesting app data failed. AppID: {app_id} CountryCode: {country_code}")
                        continue

                    backend_package = convert_steam_app_data_response_to_backend_app_data_package(
                        request_params,
                        app_data_response,
                        self.logger
                    )

                    task = asyncio.create_task(backend_session.post_app_data_package(backend_package))
                    backend_request_tasks.add(task)
                    task.add_done_callback(save_successfully_updated_app_id_and_clear_task_pool)

                done, pending = await asyncio.wait(backend_request_tasks, return_when=asyncio.FIRST_EXCEPTION)

                if exc := done.pop().exception():
                    for task in pending:
                        task.cancel()

                    self.logger.error(
                        f"Receive an error while requesting batch of apps data."
                        f" Batch of app IDs size: {len(batch_of_app_ids)} CountryCode: {country_code}"
                        f" Error: {exc}"
                        f" Amount of canceled tasks (except task with error): {len(pending)}"
                    )

                return {
                    "updated_app_ids": list(successfully_updated_app_ids),
                    "country_code": country_code
                }

        # main body ###########################

        if not (batch_of_app_ids := data.get('app_id', [])):
            self.logger.warning('Task "request_app_data": Receive empty batch of app ids')

        if not (country_code := data.get('country_code', settings.DEFAULT_COUNTRY_CODE)):
            self.logger.warning(
                f'Task "request_app_data": No country specified for batch of apps data request. '
                f'Default country selected - {country_code}'
            )

        result = self.execute_task(_task)()
        orchestrator_task_context = {
            "task_name": "update_apps_status",
            "params": {
                "app_ids": result
            }
        }
        self.register_response_task(orchestrator_task_context)
