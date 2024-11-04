import asyncio
from typing import Sized

from celery.exceptions import SoftTimeLimitExceeded

from worker.connection import steam_api_client, backend_api_client
from worker.config import settings
from worker.utils import backend_package_data_builder
from worker.logger import logger
from worker.celery_app import celery_app


# celery request tasks ###

@celery_app.task(
    name="get_app_list",
    rate_limit=settings.CELERY_TASK_COMMON_RATE_LIMIT,
    time_limit=settings.CELERY_TASK_TIME_LIMIT,
)
def get_app_list_celery_task(*args, **kwargs):
    return steam_api_client.get_app_list()


@celery_app.task(
    name="get_app_detail",
    rate_limit=settings.CELERY_TASK_COMMON_RATE_LIMIT,
    time_limit=settings.CELERY_TASK_TIME_LIMIT,
)
def get_app_detail_celery_task(*args, **kwargs):
    return steam_api_client.get_app_detail(*args, **kwargs)


# celery tasks utils ###


async def execute_celery_task(celery_task, *task_args, **task_kwargs):
    launched_celery_task = None

    try:
        launched_celery_task = celery_task.delay(*task_args, **task_kwargs)
        result = await wait_celery_task_result(launched_celery_task)
        return result, True

    except SoftTimeLimitExceeded:
        logger.error(
            f"Task {launched_celery_task if launched_celery_task else celery_task} wasn't completed on time."
        )
        return None, False

    except Exception as error:
        logger.error(
            f"An unexpected error was encountered while attempting to execute task."
            f" Task: {launched_celery_task if launched_celery_task else celery_task}"
            f" Error: {error}"
        )
        return None, False


async def wait_celery_task_result(celery_task):
    while not celery_task.ready():
        await asyncio.sleep(1)

    return celery_task.result


# worker tasks ###

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


# worker tasks utils ###

def convert_steam_app_data_response_to_backend_app_data_package(request_params, response):
    app_id = request_params.get('app_id')
    app_response = response.get(str(app_id))

    if not (is_success := app_response.get('success')):
        logger.debug(f"Request for a game id={app_id} is failed. "
                     f"Looks like game is unavailable in {request_params.get('country_code')}"
        )
        package_data = build_failed_task_package_data(request_params)

    elif not (app_data := response.get(str(app_id), {}).get('data')):
        logger.warn(f"Response to request for game id={app_id} is successful, but has no data")
        package_data = build_failed_task_package_data(request_params)

    else:
        package_data = backend_package_data_builder.build(app_data, request_params)

    return {'is_success': is_success, 'data': package_data}


def build_failed_task_package_data(request_params: dict):
    return {
        'id': request_params.get('app_id'),
        'country_code': request_params.get('country_code'),
    }
