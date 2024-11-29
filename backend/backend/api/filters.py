from mongoengine.queryset.visitor import Q

from utils.filters import (
    FilterSet,
    CustomOrderingFilterSet,
    ParamField,
    MethodParamField,
    StringFilter,
    BooleanFilter,
    MethodFilter,
    EMPTY_VALUES,
)
from django.conf import settings


class GameOrderingFilterSet(CustomOrderingFilterSet):
    class Meta:
        ordering_param = 'order_by'
        main_country = settings.DEFAULT_COUNTRY_CODE

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
    class Meta:
        main_country = settings.DEFAULT_COUNTRY_CODE

    @property
    def main_country(self):
        return self._meta.main_country

    name = StringFilter()
    is_free = BooleanFilter()
    available_in_countries__all = MethodFilter(action='filter_by_availability_in_countries__all')
    available_in_countries__any = MethodFilter(action='filter_by_availability_in_countries__any')

    discount = MethodFilter(action='filter_by_discount')
    discount__gt = MethodFilter(action='filter_by_discount__gt')
    discount__lt = MethodFilter(action='filter_by_discount__lt')

    @staticmethod
    def filter_by_discount(queryset, value, filterset, suffix=None):
        if value in EMPTY_VALUES:
            return queryset

        filtered_queryset = queryset
        for discount_size in value:
            try:
                discount_size = int(discount_size)
            except (ValueError, TypeError):
                continue

            filtered_queryset = filtered_queryset.filter(
                **{f'prices__{filterset.main_country}__price_story__0__discount{suffix}': discount_size}
            )

        return filtered_queryset

    @staticmethod
    def filter_by_discount__gt(queryset, value, filterset):
        return filterset.filter_by_discount(queryset, value, filterset, suffix='__gt')

    @staticmethod
    def filter_by_discount__lt(queryset, value, filterset):
        return filterset.filter_by_discount(queryset, value, filterset, suffix='__lt')

    @staticmethod
    def filter_by_availability_in_countries__any(queryset, value, filterset):
        if value in EMPTY_VALUES:
            return queryset

        expression = Q()
        for country in value:
            expression |= Q(**{'prices__%s__is_available' % country: True})

        return queryset(expression)

    @staticmethod
    def filter_by_availability_in_countries__all(queryset, value, filterset):
        if value in EMPTY_VALUES:
            return queryset

        expression = Q()
        for country in value:
            expression &= Q(**{'prices__%s__is_available' % country: True})

        return queryset(expression)

    # TODO: Needs converting to union currency for comparison -> key-value storage for caching&updating exchange rates
    # price = ...
    # price__gt = ...
    # price__lt = ...
