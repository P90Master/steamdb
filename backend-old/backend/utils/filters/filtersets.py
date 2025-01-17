from copy import copy

from django.utils.itercompat import is_iterable
from django.utils.translation import gettext_lazy as _
from rest_framework.filters import BaseFilterBackend
from rest_framework.settings import api_settings

from .fields import ParamField, MethodParamField


__all__ = ("FilterSet", "CustomOrderingFilterSet")


class CustomFilterMeta(type):
    def __new__(cls, name, bases, attrs):
        meta = {}

        # receive Meta attrs from parent classes
        for base in bases:
            if hasattr(base, '_meta'):
                meta.update(vars(base._meta))

        # receive Meta attrs from current class and remove Meta from attrs
        if new_meta := attrs.pop('Meta', None):
            meta.update(vars(new_meta))

        # collects current filter fields
        filter_fields = {
            field_name: field_obj for field_name, field_obj in attrs.items() if isinstance(field_obj, ParamField)
        }

        # inherit parents filter fields
        if existed_filter_fields := meta.get('_fields'):
            merged_fields = copy(existed_filter_fields)
            merged_fields.update(filter_fields)
            filter_fields = merged_fields

        # register filter fields in _meta
        meta['_fields'] = filter_fields

        # create new class and set "_meta" class that contains all inherited Meta attrs and filter fields
        new_class = super().__new__(cls, name, bases, attrs)
        new_class._meta = type('Meta', (), meta)

        # set parent class and defaults for all filter fields
        for field_name, filter_obj in filter_fields.items():
            filter_obj.set_parent_class(new_class)
            filter_obj.set_default_field_name(field_name)

        return new_class


class CoreFilter(BaseFilterBackend, metaclass=CustomFilterMeta):
    pass


# TODO: based on "rest_framework.filters.OrderingFilter" implementation. The initial implementation is inefficient in
#  this case. Need more complex refactoring of the original implementation.
class CustomOrderingFilterSet(CoreFilter):
    class Meta:
        ordering_param = api_settings.ORDERING_PARAM
        ordering_title = _('Ordering')
        ordering_description = _('Which field to use when ordering the results.')

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if not ordering:
            return queryset

        filtered_queryset = queryset

        terms_with_default_filter_in_a_row = []
        for param_name, filter_field_object in ordering:

            if isinstance(filter_field_object, MethodParamField):

                if terms_with_default_filter_in_a_row:
                    filtered_queryset = self.default_ordering_filter(
                        queryset=filtered_queryset,
                        terms=terms_with_default_filter_in_a_row,
                        filterset=self
                    )
                    terms_with_default_filter_in_a_row = []

                filtered_queryset = filter_field_object.filter(
                    queryset=filtered_queryset,
                    term=param_name,
                    filterset=self
                )

            else:
                filter_by_term = self._filter_by_term(filter_field_object, param_name)
                terms_with_default_filter_in_a_row.append(filter_by_term)

        if terms_with_default_filter_in_a_row:
            filtered_queryset = self.default_ordering_filter(
                queryset=filtered_queryset,
                terms=terms_with_default_filter_in_a_row,
                filterset=self
            )

        return filtered_queryset

    def get_ordering(self, request, queryset, view):
        """
        Ordering is set by a delimited ?ordering=... query parameter.

        The `ordering` query parameter can be overridden by setting
        the `ordering_param` value on the OrderingFilter.Meta or by
        specifying an `ORDERING_PARAM` value in the API settings.
        """
        ordering_params = request.query_params.get(self._meta.ordering_param)

        if ordering_params:
            ordering_by_fields = [param.strip() for param in ordering_params.split(',')]
            ordering = self.build_ordering(queryset, ordering_by_fields, view, request)

            if ordering:
                return ordering

        # No ordering was included, or all the ordering fields were invalid
        return self.get_default_ordering(view)

    @staticmethod
    def _filter_by_term(field_obj: ParamField, param_name: str) -> str:
        filter_by = field_obj.field_name

        if param_name.startswith("-") or param_name.startswith("+"):
            filter_by = param_name[0] + filter_by

        return filter_by

    @staticmethod
    def default_ordering_filter(queryset, terms, filterset):
        return queryset.order_by(*terms)

    def get_default_ordering(self, view):
        ordering = getattr(view, 'ordering', None)

        if isinstance(ordering, str):
            return ((ordering, None),)

        if is_iterable(ordering):
            return [(o, None) for o in ordering]

        return None

    def build_ordering(self, queryset, fields, view, request) -> list[tuple[str, ParamField]]:
        valid_fields_collection = self.get_valid_fields(queryset, view, {'request': request})

        def term_without_direction(term_):
            if term_.startswith("-") or term_.startswith("+"):
                term_ = term_[1:]

            return term_

        ordering = []
        for term in fields:
            field_name = term_without_direction(term)

            if field_name in valid_fields_collection:
                ordering.append((term, valid_fields_collection[field_name]))

        return ordering

    def get_valid_fields(self, queryset, view, context=None) -> dict[str, ParamField]:
        if context is None:
            context = {}

        valid_fields_collection = self._meta._fields

        if not valid_fields_collection:
            return self.get_default_valid_fields(queryset, view, context)

        return valid_fields_collection

    def get_default_valid_fields(self, queryset, view, context=None):
        # TODO: get from rest_framework.filters - adapt for working with MongoEngine documents
        return {}


class FilterSet(CoreFilter):
    def filter_queryset(self, request, queryset, view):
        filters = self.get_filters(request, view)

        if not filters:
            return queryset

        filtered_queryset = queryset
        for filter_obj, values in filters:
            if isinstance(filter_obj, MethodParamField):
                filtered_queryset = filter_obj.filter(filtered_queryset, values, self)
                continue

            for value in values:
                filtered_queryset = filter_obj.filter(filtered_queryset, value, self)

        return filtered_queryset

    def get_filters(self, request, view):
        valid_filters_collection = self._meta._fields

        valid_filters_in_request = [
            (
                valid_filters_collection[param_name],
                self.clean_filter_value(request.query_params.getlist(param_name))
            )
            for param_name in request.query_params
            if param_name in valid_filters_collection
        ]

        return valid_filters_in_request if valid_filters_in_request else self.get_default_filters(view)

    @staticmethod
    def clean_filter_value(values: list[str]):
        # In fact, if we get several values for one filter, then with 95% probability they are either mutually
        # exclusive or repeated. However, we must remember about this possibility, and in a situation where
        # we have 2 filter values, one of which specifies the queryset more strongly, we must take it into account.
        # Therefore, we cannot discard several values, leaving only 1.

        cleaned_values = []
        for value in values:
            cleaned_values.extend([param.strip() for param in value.split(',')])

        return cleaned_values

    def get_default_filters(self, view):
        filters = getattr(view, 'default_filters', None)

        # TODO: default_filters - FilterSet - set of StaticFilter filters that are always applied
        # TODO: StaticFilter - FilterField with const value

        return None
