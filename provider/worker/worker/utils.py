from worker.settings import CountryCodeCurrencyMapping


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
