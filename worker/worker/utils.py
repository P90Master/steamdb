from worker.config import CountryCodeCurrencyMapping
from worker.logger import logger


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


class BackendPackageDataBuilder:
    def __init__(self):
        self.backend_package_data_build_schema = {
            "id": self._extract_app_id,
            "name": self._extract_app_name,
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
    def _extract_app_price(app_data, *args, **kwargs):
        if app_data.get('is_free'):
            return 0

        return float(app_data.get('price_overview', {}).get('final')) / 100.0

    @staticmethod
    def _extract_app_discount(app_data, *args, **kwargs):
        if app_data.get('is_free'):
            return 0

        return app_data.get('price_overview', {}).get('discount_percent')

    @staticmethod
    def _extract_response_country_code(app_data, app_request_params, *args, **kwargs):
        return app_request_params.get('country_code')

    @staticmethod
    def _extract_response_currency(app_data, app_request_params, *args, **kwargs):
        if app_data.get('is_free'):
            country_code = app_request_params.get('country_code')
            return CountryCodeCurrencyMapping.get(country_code)

        return app_data.get('price_overview', {}).get('currency')


backend_package_data_builder = BackendPackageDataBuilder()
