from utils.filters import CustomOrderingFilter, FilterField, MethodFilterField
from utils.enums import CountryCodes


class GameOrderingFilter(CustomOrderingFilter):
    class Meta:
        ordering_param = 'ordering'
        main_country = CountryCodes.united_states.value

    @property
    def main_country(self):
        return self._meta.main_country

    total_recommendations = FilterField()
    discount = MethodFilterField(action='order_by_discount')
    last_updated = MethodFilterField(action='order_by_last_updating_date')

    @staticmethod
    def order_by_discount(queryset, term, request, filterset):
        direction = '-' if term.startswith('-') else ''
        # Agreement that a game entry in the context of country <main_country> is likely to exist
        return queryset.order_by(f'{direction}prices__{filterset.main_country}__price_story__0__discount')

    @staticmethod
    def order_by_last_updating_date(queryset, term, request, filterset):
        direction = '-' if term.startswith('-') else ''
        # Agreement that a game entry in the context of country <main_country> is likely to exist
        return queryset.order_by(f'{direction}prices__{filterset.main_country}__price_story__0__timestamp')
