from .consts import DEFAULT_LOOKUP_EXPRESSION, EMPTY_VALUES, NULL_CHOICE_VALUE


__all__ = (
    "ParamField",
    "MethodParamField",
    "FilterField",
    "NumberFilter",
    "StringFilter",
    "CharFilter",
    "DateFilter",
    "BooleanFilter",
    "ChoiceFilter",
    "MethodFilter",
)


class ParamField:
    def __init__(self, field_name=None):
        self.field_name = field_name
        self.parent_class = None

    def set_parent_class(self, parent_class):
        self.parent_class = parent_class

    def set_default_field_name(self, field_name):
        if self.field_name is None:
            self.field_name = field_name


class MethodParamField(ParamField):
    def __init__(self, action: str, *args, **kwargs):
        self._parent_action_name = action
        self.action = None
        super().__init__(*args, **kwargs)

    def filter(self, queryset, term, filterset):
        """
        This is a proxy for the actual method that defined in parent class.
        """

        # cause filter object initiates before filterset class
        if not self.action:
            self.action = getattr(self.parent_class, self._parent_action_name, None)

        return self.action(queryset, term, filterset) if self.action else queryset


class FilterField(ParamField):
    def __init__(self, lookup_expr=None, *args, distinct=False, exclude=False, **kwargs):
        if lookup_expr is None:
            lookup_expr = DEFAULT_LOOKUP_EXPRESSION

        self.lookup_expr = lookup_expr
        self.distinct = distinct
        self.exclude = exclude
        super().__init__(*args, **kwargs)

    def get_method(self, queryset):
        return queryset.exclude if self.exclude else queryset.filter

    def filter(self, queryset, value, filterset=None):
        if value in EMPTY_VALUES:
            return queryset

        if self.distinct:
            queryset = queryset.distinct()

        lookup = "%s%s" % (self.field_name, ('__'+ self.lookup_expr) if self.lookup_expr else '')
        return self.get_method(queryset)(**{lookup: value})


class MethodFilter(MethodParamField):
    """
    Just renamed copy of MethodParamField
    """

    def filter(self, queryset, value, filterset):
        return super().filter(queryset, value, filterset)


class NumberFilter(FilterField):
    pass


class StringFilter(FilterField):
    def __init__(self, *args, **kwargs):
        # field contains whole word case-insensitive
        kwargs.setdefault("lookup_expr", 'iwholeword')
        super().__init__(*args, **kwargs)


class CharFilter(FilterField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("lookup_expr", 'icontains')
        super().__init__(*args, **kwargs)


class BooleanFilter(FilterField):
    def filter(self, queryset, value):
        if value in EMPTY_VALUES:
            return queryset

        if self.distinct:
            queryset = queryset.distinct()

        lookup = "%s%s" % (self.field_name, ('__' + self.lookup_expr) if self.lookup_expr else '')
        return self.get_method(queryset)(**{lookup: str(value).lower() in ('1', 'true')})


class DateFilter(FilterField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("lookup_expr", 'year')
        super().__init__(*args, **kwargs)


class ChoiceFilter(FilterField):
    def __init__(self, *args, **kwargs):
        self.null_value = kwargs.get("null_value", NULL_CHOICE_VALUE)
        super().__init__(*args, **kwargs)

    def filter(self, queryset, value, filterset=None):
        if value != self.null_value:
            return super().filter(queryset, value)

        queryset = self.get_method(queryset)(
            **{"%s%s" % (self.field_name, ('__'+ self.lookup_expr) if self.lookup_expr else ''): None}
        )
        return queryset.distinct() if self.distinct else queryset
