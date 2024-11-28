from copy import copy

from django.utils.itercompat import is_iterable
from django.utils.translation import gettext_lazy as _
from rest_framework.filters import BaseFilterBackend
from rest_framework.settings import api_settings


class FilterField:
    def __init__(self, document_field_name=None):
        self.document_field_name = document_field_name
        self.parent_class = None

    def set_parent_class(self, parent_class):
        self.parent_class = parent_class

    def set_default_document_field_name(self, document_field_name):
        if self.document_field_name is None:
            self.document_field_name = document_field_name


class MethodFilterField(FilterField):
    def __init__(self, action: str, *args, **kwargs):
        self._parent_action_name = action
        self.action = None
        super().__init__(*args, **kwargs)

    def filter(self, queryset, request):
        """
        This is a proxy for the actual method that defined in parent class.
        """
        if not self.action:
            self.action = getattr(self.parent_class, self._parent_action_name, None)

        return self.action(queryset, request) if self.action else queryset


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
            field_name: field_obj for field_name, field_obj in attrs.items() if isinstance(field_obj, FilterField)
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
            filter_obj.set_default_document_field_name(field_name)

        return new_class


class CustomFilter(BaseFilterBackend, metaclass=CustomFilterMeta):
    pass


# TODO: filter_queryset -> get_ordering -> remove_invalid_fields (now "build_ordering") -> get_valid_fields pipeline
#  based on "rest_framework.filters.OrderingFilter" implementation. The initial implementation is inefficient in this
#  case. Need to abandon the original implementation in favor of an implementation similar to django_filters.
class CustomOrderingFilter(CustomFilter):
    class Meta:
        ordering_param = api_settings.ORDERING_PARAM
        ordering_title = _('Ordering')
        ordering_description = _('Which field to use when ordering the results.')

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

    def get_default_ordering(self, view):
        ordering = getattr(view, 'ordering', None)

        if isinstance(ordering, str):
            return ((ordering, None),)

        if is_iterable(ordering):
            return [(o, None) for o in ordering]

        return None

    def get_default_valid_fields(self, queryset, view, context=None):
        # TODO: get from rest_framework.filters - adapt for working with MongoEngine documents
        return {}

    def build_ordering(self, queryset, fields, view, request) -> list[tuple[str, FilterField]]:
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

    def get_valid_fields(self, queryset, view, context=None) -> dict[str, FilterField]:
        if context is None:
            context = {}

        valid_fields_collection = self._meta._fields

        if not valid_fields_collection:
            return self.get_default_valid_fields(queryset, view, context)

        return valid_fields_collection

    @staticmethod
    def _filter_by_term(field_obj: FilterField, param_name: str) -> str:
        filter_by = field_obj.document_field_name

        if param_name.startswith("-") or param_name.startswith("+"):
            filter_by = param_name[0] + filter_by

        return filter_by

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if not ordering:
            return queryset

        filtered_queryset = queryset

        terms_with_default_filter_in_a_row = []
        for param_name, filter_field_object in ordering:

            if isinstance(filter_field_object, MethodFilterField):

                if terms_with_default_filter_in_a_row:
                    filtered_queryset = self.default_ordering_filter(
                        filtered_queryset,
                        terms_with_default_filter_in_a_row,
                        request
                    )
                    terms_with_default_filter_in_a_row = []

                filtered_queryset = filter_field_object.filter(filtered_queryset, request)

            else:
                filter_by_term = self._filter_by_term(filter_field_object, param_name)
                terms_with_default_filter_in_a_row.append(filter_by_term)

        if terms_with_default_filter_in_a_row:
            filtered_queryset = self.default_ordering_filter(
                filtered_queryset,
                terms_with_default_filter_in_a_row,
                request
            )

        return filtered_queryset

    def default_ordering_filter(self, queryset, terms, request):
        return queryset.order_by(*terms)
