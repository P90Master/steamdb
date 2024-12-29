from collections import defaultdict
from collections.abc import Callable, Mapping
from typing import Any, Optional, Union

from beanie import SortDirection
from beanie.odm.interfaces.find import FindType
from beanie.odm.queries.find import FindMany
from pydantic import ValidationInfo, field_validator

from fastapi_filter.base.filter import BaseFilterModel


METHOD_OPERATOR_KEY = "method"

_odm_operator_transformer: dict[str, Callable[[Optional[str]], Optional[dict[str, Any]]]] = {
    "neq": lambda value: {"$ne": value},
    "gt": lambda value: {"$gt": value},
    "gte": lambda value: {"$gte": value},
    "in": lambda value: {"$in": value},
    "isnull": lambda value: None if value else {"$ne": None},
    "lt": lambda value: {"$lt": value},
    "lte": lambda value: {"$lte": value},
    "not": lambda value: {"$ne": value},
    "ne": lambda value: {"$ne": value},
    "not_in": lambda value: {"$nin": value},
    "nin": lambda value: {"$nin": value},
    "like": lambda value: {"$regex": f".*{value}.*"},
    "ilike": lambda value: {"$regex": f".*{value}.*", "$options": "i"},
    "exists": lambda value: {"$exists": value},
}


class Filter(BaseFilterModel):
    class Constants:  # pragma: no cover
        model: Any
        ordering_field_name: str = "order_by"
        search_model_fields: list[str]
        search_field_name: str = "search"
        prefix: str
        original_filter: type["BaseFilterModel"]
        custom_ordering_fields: tuple[str] = ()

    def sort(self, query: FindMany[FindType]) -> FindMany[FindType]:
        if not self.ordering_values:
            return query

        custom_ordering_methods: list[tuple[callable, SortDirection]] = []
        common_ordering_by_fields: list[tuple[str, SortDirection]] = []

        for field_name_with_direction in self.ordering_values:
            field_name = field_name_with_direction.replace('+', '').replace('-', '')
            direction = SortDirection.ASCENDING if field_name_with_direction.startswith('+') \
                else SortDirection.DESCENDING

            if field_name in self.Constants.custom_ordering_fields:
                try:
                    custom_ordering_methods.append((getattr(self, 'sort__' + field_name), direction))
                except AttributeError:
                    pass
                finally:
                    continue

            common_ordering_by_fields.append((field_name, direction))

        for ordering_method, direction in custom_ordering_methods:
            query = ordering_method(query, direction)

        return query.sort(*common_ordering_by_fields)

    @field_validator("*", mode="before", check_fields=False)
    def validate_order_by(cls, value, field: ValidationInfo):
        if field.field_name != cls.Constants.ordering_field_name:
            return value

        if not value:
            return None

        field_name_usages = defaultdict(list)
        duplicated_field_names = set()

        for field_name_with_direction in value:
            field_name = field_name_with_direction.strip().replace("-", "").replace("+", "")

            if not hasattr(cls.Constants.model, field_name) and field_name not in cls.Constants.custom_ordering_fields:
                raise ValueError(f"{field_name} is not a valid ordering field.")

            field_name_usages[field_name].append(field_name_with_direction)
            if len(field_name_usages[field_name]) > 1:
                duplicated_field_names.add(field_name)

        if duplicated_field_names:
            ambiguous_field_names = ", ".join(
                [
                    field_name_with_direction
                    for field_name in sorted(duplicated_field_names)
                    for field_name_with_direction in field_name_usages[field_name]
                ]
            )
            raise ValueError(
                f"Field names can appear at most once for {cls.Constants.ordering_field_name}. "
                f"The following was ambiguous: {ambiguous_field_names}."
            )

        return value

    @field_validator("*", mode="before")
    @classmethod
    def split_str(
        cls: type["BaseFilterModel"], value: Optional[str], field: ValidationInfo
    ) -> Optional[Union[list[str], str]]:
        if (
            field.field_name is not None
            and (
                field.field_name == cls.Constants.ordering_field_name
                or field.field_name.endswith("__in")
                or field.field_name.endswith("__nin")
            )
            and isinstance(value, str)
        ):
            if not value:
                return []

            return list(value.split(","))

        return value

    def _get_filter_conditions(self, nesting_depth: int = 1) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]:
        filter_conditions: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []

        for field_name, value in self.filtering_fields:
            field_value = getattr(self, field_name)

            if isinstance(field_value, Filter):
                if not field_value.model_dump(exclude_none=True, exclude_unset=True):
                    continue

                filter_conditions.append(
                    (
                        {field_name: _odm_operator_transformer["neq"](None)},
                        {"fetch_links": True, "nesting_depth": nesting_depth},
                    )
                )

                for part, part_options in field_value._get_filter_conditions(nesting_depth=nesting_depth + 1):  # noqa: SLF001
                    for sub_field_name, sub_value in part.items():
                        filter_conditions.append(
                            (
                                {f"{field_name}.{sub_field_name}": sub_value},
                                {"fetch_links": True, "nesting_depth": nesting_depth, **part_options},
                            )
                        )

            elif "__" in field_name:
                stripped_field_name, operator = field_name.split("__")

                if operator == METHOD_OPERATOR_KEY:
                    continue

                search_criteria = _odm_operator_transformer[operator](value)
                filter_conditions.append(({stripped_field_name: search_criteria}, {}))

            elif field_name == self.Constants.search_field_name and hasattr(self.Constants, "search_model_fields"):
                search_conditions = [
                    {search_field: _odm_operator_transformer["ilike"](value)}
                    for search_field in self.Constants.search_model_fields
                ]
                filter_conditions.append(({"$or": search_conditions}, {}))

            else:
                filter_conditions.append(({field_name: value}, {}))

        return filter_conditions

    def _get_method_filters(self) -> list[tuple[Callable, Any]]:
        methods: list[tuple[Callable, Any]] = []

        for field_name, value in self.filtering_fields:
            if "__" not in field_name:
                continue

            stripped_field_name, operator = field_name.split("__")

            if operator != METHOD_OPERATOR_KEY:
                continue

            filter_method = getattr(self, 'filter__' + stripped_field_name, None)

            if filter_method is None:
                continue

            methods.append((filter_method, value))

        return methods

    def filter(self, query: FindMany[FindType]) -> FindMany[FindType]:
        plain_filters = self._get_filter_conditions()
        method_filters = self._get_method_filters()

        for filter_condition, filter_kwargs in plain_filters:
            query = query.find(filter_condition, **filter_kwargs)

        for (method, value) in method_filters:
            query = method(query, value)

        return query.find(fetch_links=True)
