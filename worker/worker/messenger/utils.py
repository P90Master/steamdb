import asyncio
import functools

from worker.config import CountryCodeSteamCurrencyMapping


class HandledException(Exception):
    pass


def trace_logs(decorated):
    @functools.wraps(decorated)
    def sync_wrapper(self, *args, **kwargs):
        task_name = decorated.__name__
        if not hasattr(self, 'logger'):
            raise AttributeError(f"Decorated method {task_name} doesn't have logger")

        self.logger.info(f"Received command to execute task: {task_name}")

        try:
            result = decorated(self, *args, **kwargs)

        except HandledException as handled_exception:
            raise handled_exception

        except Exception as error:
            error_message = f'Task "{task_name}" execution failed with error: {error}'
            self.logger.error(error_message)
            raise HandledException(error_message)

        else:
            self.logger.info(f"Task executed: {task_name}")
            return result

    async def async_wrapper(self, *args, **kwargs):
        task_name = decorated.__name__
        if not hasattr(self, 'logger'):
            raise AttributeError(f"Decorated method {task_name} doesn't have logger")

        self.logger.info(f"Received command to execute task: {task_name}")

        try:
            result = await decorated(self, *args, **kwargs)

        except HandledException as handled_exception:
            raise handled_exception

        except Exception as error:
            error_message = f'Task "{task_name}" execution failed with error: {error}'
            self.logger.error(error_message)
            raise HandledException(error_message)

        else:
            self.logger.info(f"Task executed: {task_name}")
            return result

    return async_wrapper if asyncio.iscoroutinefunction(decorated) else sync_wrapper


def convert_steam_app_data_response_to_backend_app_data_package(request_params, response, logger):
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


class BackendPackageDataBuilder:
    def __init__(self):
        self.backend_package_data_build_schema = {
            "id": self._extract_app_id,
            "name": self._extract_app_name,
            "type": self._extract_app_type,
            "is_free": self._extract_app_is_free,
            "short_description": self._extract_app_short_description,
            "developers": self._extract_app_developers,
            "publishers": self._extract_app_publishers,
            "total_recommendations": self._extract_app_total_recommendations,
            "country_code": self._extract_response_country_code,
            "currency": self._extract_response_currency,
            "discount": self._extract_app_discount,
            "price": self._extract_app_price
        }

    def build(self, app_data, app_request_params):
        return {
            field_name: data_extractor(app_data, app_request_params)
            for field_name, data_extractor in self.backend_package_data_build_schema.items()
        }

    @staticmethod
    def _extract_app_id(app_data, *args, **kwargs):
        return app_data.get('steam_appid')

    @staticmethod
    def _extract_app_name(app_data, *args, **kwargs):
        return app_data.get('name')

    @staticmethod
    def _extract_app_type(app_data, *args, **kwargs):
        return app_data.get('type')

    @staticmethod
    def _extract_app_is_free(app_data, *args, **kwargs):
        flag = app_data.get('is_free', False)
        return flag if isinstance(flag, bool) else str(flag).lower() == 'true'

    @staticmethod
    def _extract_app_short_description(app_data, *args, **kwargs):
        return app_data.get('short_description', '')

    @staticmethod
    def _extract_app_developers(app_data, *args, **kwargs):
        return app_data.get('developers', [])

    @staticmethod
    def _extract_app_publishers(app_data, *args, **kwargs):
        return app_data.get('publishers', [])

    @staticmethod
    def _extract_app_total_recommendations(app_data, *args, **kwargs):
        return app_data.get('recommendations', {}).get('total', 0)

    @staticmethod
    def _extract_app_price(app_data, *args, **kwargs):
        if app_data.get('is_free'):
            return 0

        return float(app_data.get('price_overview', {}).get('final', 0)) / 100.0

    @staticmethod
    def _extract_app_discount(app_data, *args, **kwargs):
        if app_data.get('is_free'):
            return 0

        return app_data.get('price_overview', {}).get('discount_percent', 0)

    @staticmethod
    def _extract_response_country_code(app_data, app_request_params, *args, **kwargs):
        return app_request_params.get('country_code')

    @staticmethod
    def _extract_response_currency(app_data, app_request_params, *args, **kwargs):
        if app_data.get('is_free'):
            country_code = app_request_params.get('country_code')
            return CountryCodeSteamCurrencyMapping.get(country_code)

        return app_data.get('price_overview', {}).get('currency')


backend_package_data_builder = BackendPackageDataBuilder()
