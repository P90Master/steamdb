from utils.filters import (
    FilterSet,
    CustomOrderingFilterSet,
    ParamField,
    MethodParamField,
    StringFilter,
    BooleanFilter,
)
from utils.enums import CountryCodes


class GameOrderingFilterSet(CustomOrderingFilterSet):
    class Meta:
        ordering_param = 'order_by'
        main_country = CountryCodes.united_states.value

    @property
    def main_country(self):
        return self._meta.main_country

    total_recommendations = ParamField()
    discount = MethodParamField(action='order_by_discount')
    last_updated = MethodParamField(action='order_by_last_updating_date')

    @staticmethod
    def order_by_discount(queryset, term, filterset):
        direction = '-' if term.startswith('-') else ''
        # Agreement that a game entry in the context of country <main_country> is likely to exist
        return queryset.order_by(f'{direction}prices__{filterset.main_country}__price_story__0__discount')

    @staticmethod
    def order_by_last_updating_date(queryset, term, filterset):
        direction = '-' if term.startswith('-') else ''
        # Agreement that a game entry in the context of country <main_country> is likely to exist
        return queryset.order_by(f'{direction}prices__{filterset.main_country}__price_story__0__timestamp')


class GameFilterSet(FilterSet):
    name = StringFilter()
    is_free = BooleanFilter()
    # TODO: MethodFilter cause of complex logic
    # available_in_countries = ListFilter(lookup_expr='in')

    # TODO: MethodFilter cause of complex logic
    # TODO: Needs converting to union currency for comparison -> key-value storage for caching&updating exchange rates
    # price = NumberFilter()
    # price__gt =NumberFilter(field_name='price', lookup_expr='gt')
    # price__lt = NumberFilter(field_name='price', lookup_expr='lt')

    # TODO: MethodFilter cause of complex logic
    # discount = NumberFilter()
    # discount__gt = NumberFilter(field_name='price', lookup_expr='gt')
    # discount__lt = NumberFilter(field_name='price', lookup_expr='lt')
