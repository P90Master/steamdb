import asyncio
import functools
import json
from logging import Logger
from typing import Any, Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties, Basic

from worker.core.config import settings
from worker.core.logger import get_logger
from worker.celery import execute_celery_task, get_app_list_celery_task, get_app_detail_celery_task
from worker.api import SteamAPIClient, AsyncBackendAPIClient
from .utils import convert_steam_app_data_response_to_backend_app_data_package, trace_logs, HandledException


class TaskManagerMeta(type):
    def __new__(cls, name: str, bases: tuple[type], attrs: dict[str, Any]) -> type:
        new_class = super().__new__(cls, name, bases, attrs)
        new_class._receive_tasks = {}

        for attr_name, attr_value in attrs.items():
            if callable(attr_value) and attr_name.startswith('receive_task__'):
                task_name =  attr_name[attr_name.rfind("__") + 2:]
                new_class._receive_tasks[task_name] = attr_value

        return new_class


class TaskManager(metaclass=TaskManagerMeta):
    DEFAULT_MESSAGE_PRIORITY: int = 1

    def __init__(
        self,
        messenger_channel: BlockingChannel,
        backend_api_client: AsyncBackendAPIClient,
        steam_api_client: SteamAPIClient,
        logger: Logger = None
    ):
        self.messenger_channel = messenger_channel
        self.backend_api_client = backend_api_client
        self.steam_api_client = steam_api_client
        self.logger = logger if logger else get_logger(settings, __name__)

    def execute_task(self, task: callable) -> callable:
        @functools.wraps(task)
        def wrapper(*args, **kwargs) -> Any:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(task(self, **kwargs))

        return wrapper

    def get_receive_task_handler(self, task_name: str) -> Optional[callable]:
        return self._receive_tasks.get(task_name)

    def register_task(self, task_context: dict[str, Any], message_priority: int = 1):
        context_json_payload = json.dumps(task_context)
        if message_priority is None:
            message_priority = self.DEFAULT_MESSAGE_PRIORITY

        self.messenger_channel.basic_publish(
            exchange='',
            routing_key=settings.RABBITMQ_OUTCOME_QUERY,
            body=context_json_payload,
            properties=pika.BasicProperties(
                delivery_mode=2,
                priority=message_priority
            )
        )

    def handle_received_task_message(
            self, ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes):
        data = json.loads(body)

        if not (requested_task_name := data.get('task_name')):
            # TODO: id of message & logging it (broker deletes messages - save wrong messages for debug?)
            self.logger.error('Message received from orchestrator doesnt contain "task_name". Message discarded.')
            ch.basic_reject(delivery_tag=method.delivery_tag)
            return

        if not (handle_received_task := self.get_receive_task_handler(requested_task_name)):
            self.logger.error(f'Message received from orchestrator contains an invalid task name '
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
            ch.basic_ack(delivery_tag=method.delivery_tag)

    @trace_logs
    def receive_task__request_apps_list(
            self, ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, task_params: dict[str, Any]):
        async def _task(*args, **kwargs) -> list[str]:
            self.logger.info('Task "request_apps_list": Start execution.')

            apps_collection, is_success = await execute_celery_task(celery_task=get_app_list_celery_task)
            if not is_success:
                error_msg = 'Task "request_apps_list": Requesting apps list failed. Execution interrupted.'
                self.logger.error(error_msg)
                raise HandledException(error_msg)

            app_list = [app.get('appid') for app in apps_collection.get('applist', {}).get('apps', {})]
            self.logger.info('Task "request_apps_list": Apps list successfully requested. Completion of execution.')
            return app_list

        result = self.execute_task(_task)()
        orchestrator_task_context = {
            # TODO: task names as settings consts
            "task_name": "actualize_app_list",
            "params": {
                "app_ids": result
            }
        }
        self.register_task(orchestrator_task_context, message_priority=properties.priority)

    @trace_logs
    def receive_task__request_app_data(
            self, ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, task_params: dict[str, Any]):
        async def _task(*args, **kwargs):
            self.logger.info(f'Task request_app_data": Start execution.')
            self.logger.debug(f'Task "request_app_data": Requested AppID: {app_id} CountryCode: {country_code}')

            request_params = {'app_id': app_id, 'country_code': country_code}
            app_data_response, is_success = await execute_celery_task(
                celery_task=get_app_detail_celery_task,  # type: ignore
                **request_params
            )
            if not is_success:
                error_message = f'Task "request_app_data": Requesting app data from steam failed. Execution interrupted'
                self.logger.error(error_message)
                self.logger.debug(
                    f'Task "request_app_data": Failed request for AppID: {app_id} CountryCode: {country_code}'
                )
                raise HandledException(error_message)

            backend_package = convert_steam_app_data_response_to_backend_app_data_package(
                request_params,
                app_data_response,
                self.logger
            )
            try:
                await self.backend_api_client.post_app_data_package(backend_package)

            except Exception as unhandled_error:
                error_message = (
                    # TODO: 'Task "request_app_data": ' prefix in consts
                    f'Task "request_app_data": Receive an error while requesting app data.'
                    f" App ID: {app_id} CountryCode: {country_code}"
                    f" Error: {unhandled_error}"
                )
                self.logger.error(error_message)
                raise HandledException(error_message)

            self.logger.info(f'Task "request_app_data": App data successfully requested. Completion of execution.')

        # main body ###########################

        if not (app_id := task_params.get('app_id')):
            error_msg = 'Task "request_app_data": No app_id specified in task context'
            self.logger.error(error_msg)
            raise HandledException(error_msg)

        if not (country_code := task_params.get('country_code', settings.DEFAULT_COUNTRY_CODE)):
            self.logger.warning(
                f'Task "request_app_data": No country specified for app_id {app_id} data request. '
                f'Default country selected - {country_code}'
            )

        self.execute_task(_task)()
        orchestrator_task_context = {
            "task_name": "update_apps_status",
            "params": {
                "app_ids": [app_id]
            }
        }
        self.register_task(orchestrator_task_context, message_priority=properties.priority)

    @trace_logs
    def receive_task__bulk_request_for_apps_data(
            self, ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, task_params):
        async def _task(*args, **kwargs):
            self.logger.info(
                f'Task "bulk_request_for_apps_data":'
                f' Batch of app IDs size: {len(batch_of_app_ids)} country codes: {country_codes}'
            )

            backend_request_tasks = set()
            successfully_updated_app_ids = set()

            def save_successfully_updated_app_id_and_clear_task_pool(backend_task: asyncio.Task):
                # TODO: if task has exception (because of it asyncio.wait stopped and this in done) ?
                backend_request_tasks.discard(backend_task)
                updated_app_id = (backend_task.result() or {}).get('data', {}).get('id')
                if updated_app_id:
                    successfully_updated_app_ids.add(updated_app_id)

            async with self.backend_api_client as backend_session:
                for app_id in batch_of_app_ids:
                    for country_code in country_codes:
                        request_params = {
                            'app_id': app_id,
                            'country_code': country_code
                        }

                        app_data_response, is_success = await execute_celery_task(
                            celery_task=get_app_detail_celery_task,  # type: ignore
                            **request_params
                        )
                        if not is_success:
                            self.logger.warning(
                                f'Task "bulk_request_for_apps_data":'
                                f' Requesting app "{app_id}" with country code "{country_code}" failed'
                            )
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
                        f'Task "bulk_request_for_apps_data": Receive an error.'
                        f" Batch of app IDs size: {len(batch_of_app_ids)} Country Codes: {country_codes}"
                        f" Error: {exc}"
                        f" Amount of canceled tasks (except task with error): {len(pending)}"
                    )

                return list(successfully_updated_app_ids)

        # main body ###########################

        if not (batch_of_app_ids := task_params.get('app_ids', [])):
            self.logger.warning('Task "bulk_request_for_apps_data": Receive empty batch of app ids')

        if not (country_codes := task_params.get('country_code', settings.DEFAULT_COUNTRY_BUNDLE)):
            self.logger.warning(
                f'Task "bulk_request_for_apps_data": No country specified for batch of apps data request. '
                f'Default country bundle selected - {country_codes}'
            )

        result = self.execute_task(_task)()
        orchestrator_task_context = {
            "task_name": "update_apps_status",
            "params": {
                "app_ids": result
            }
        }
        self.register_task(orchestrator_task_context, message_priority=properties.priority)
