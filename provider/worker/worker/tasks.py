import asyncio
from typing import Sized

from worker.connection import steam_api_client, backend_api_client
from worker.settings import DEFAULT_COUNTRY_CODE
from worker.utils import backend_package_data_builder
from worker.logger import logger


class WrongSteamResponseError(Exception):
    pass


def build_failed_task_package_data(request_params: dict):
    return {
        'id': request_params.get('app_id'),
        'country_code': request_params.get('country_code'),
    }


def convert_steam_app_data_response_to_backend_app_data_package(request_params, response):
    app_id = request_params.get('app_id')
    app_response = response.get(str(app_id))

    if not (is_success := app_response.get('success')):
        # TODO info log message
        package_data = build_failed_task_package_data(request_params)

    else:
        if not (app_data := response.get(str(app_id), {}).get('data')):
            # TODO Handle this
            raise WrongSteamResponseError(f"Response to request for game id={app_id} is successful, but has no data")

        package_data = backend_package_data_builder.build(app_data, request_params)

    return {'is_success': is_success, 'data': package_data}


async def request_all_apps_task():
    # TODO wrap steam requests in celery task
    logger.info('Requesting apps list..')
    apps_collection = await steam_api_client.get_app_list()
    app_list = [app.get('appid') for app in apps_collection.get('applist', {}).get('apps', {})]
    logger.info('Apps list successfully requested')
    return app_list


async def update_app_data_task(app_id: str, country_code: str = DEFAULT_COUNTRY_CODE):
    # TODO wrap steam requests in celery task

    logger.info(f'Requesting app data. AppID: {app_id} CountryCode: {country_code}')

    request_params = {
        'app_id': app_id,
        'country_code': country_code
    }

    app_data_response = await steam_api_client.get_app_detail(**request_params)
    logger.info(f'App data requested successfully. AppID: {app_id} CountryCode: {country_code}')
    backend_package = convert_steam_app_data_response_to_backend_app_data_package(request_params, app_data_response)
    await backend_api_client.post_app_data_package(backend_package)
    logger.info(f'App data successfully pushed to backend. AppID: {app_id} CountryCode: {country_code}')


async def batch_update_apps_data_task(batch_of_app_ids: Sized, country_code: str = DEFAULT_COUNTRY_CODE):
    # TODO TODO wrap steam requests in celery task

    logger.info(
        f'Requesting batch of apps data.'
        f' Batch of app IDs size: {len(batch_of_app_ids)} CountryCode: {country_code}'
    )

    backend_request_tasks = set()

    async with backend_api_client as backend_session:
        for app_id in batch_of_app_ids:
            request_params = {
                'app_id': app_id,
                'country_code': country_code
            }

            app_data_response = await steam_api_client.get_app_detail(**request_params)
            backend_package = convert_steam_app_data_response_to_backend_app_data_package(
                request_params,
                app_data_response
            )

            task = asyncio.create_task(backend_session.post_app_data_package(backend_package))
            backend_request_tasks.add(task)
            task.add_done_callback(backend_request_tasks.discard)

        done, pending = await asyncio.wait(backend_request_tasks, return_when=asyncio.FIRST_EXCEPTION)
        if pending and (exc := pending.pop().exception()):
            for task in pending:
                task.cancel()

            # TODO error log about failed ones
            raise exc
