import asyncio
from typing import Sized

from worker.connections import steam_api_client, backend_api_client
from worker.config import settings
from worker.utils import convert_steam_app_data_response_to_backend_app_data_package, execute_celery_task
from worker.logger import logger
from worker.celery import execute_celery_task, get_app_list_celery_task, get_app_detail_celery_task


async def request_all_apps_task():
    # TODO: wrap steam requests in celery task
    logger.info('Requesting apps list..')

    apps_collection, is_success = await execute_celery_task(celery_task=get_app_list_celery_task)
    if not is_success:
        logger.error("Requesting apps list failed")
        return []

    app_list = [app.get('appid') for app in apps_collection.get('applist', {}).get('apps', {})]
    logger.info('Apps list successfully requested')
    return app_list


async def update_app_data_task(app_id: str, country_code: str = settings.DEFAULT_COUNTRY_CODE):
    # TODO: wrap steam requests in celery task

    logger.info(f'Requesting app data. AppID: {app_id} CountryCode: {country_code}')

    request_params = {
        'app_id': app_id,
        'country_code': country_code
    }

    app_data_response, is_success = await execute_celery_task(celery_task=get_app_detail_celery_task, **request_params)
    if not is_success:
        logger.error(f"Requesting app data failed. AppID: {app_id} CountryCode: {country_code}")
        return

    logger.info(f'App data requested successfully. AppID: {app_id} CountryCode: {country_code}')

    backend_package = convert_steam_app_data_response_to_backend_app_data_package(request_params, app_data_response)
    await backend_api_client.post_app_data_package(backend_package)
    logger.info(f'App data successfully pushed to backend. AppID: {app_id} CountryCode: {country_code}')


async def batch_update_apps_data_task(batch_of_app_ids: Sized, country_code: str = settings.DEFAULT_COUNTRY_CODE):
    # TODO: wrap steam requests in celery task

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
            task.add_done_callback(backend_request_tasks.discard)

        done, pending = await asyncio.wait(backend_request_tasks, return_when=asyncio.FIRST_EXCEPTION)
        if pending:
            for task in pending:
                task.cancel()

            exc = done.pop().exception()

            logger.error(
                f"Receive an error while requesting batch of apps data."
                f" Batch of app IDs size: {len(batch_of_app_ids)} CountryCode: {country_code}"
                f" Error: {exc}"
                f" Amount of successful tasks: {len(done)}"
                f" Amount of canceled tasks: {len(pending)}"
            )
