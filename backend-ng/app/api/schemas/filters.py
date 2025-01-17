from typing import Optional, Annotated

from beanie import SortDirection
from pydantic import Field
from beanie.odm.interfaces.find import FindType
from beanie.odm.queries.find import FindMany

from app.utils.filters import Filter
from app.utils.ftsearch_index import Index
from app.core.config import settings
from app.models import App


class AppFilter(Filter):
    name: Optional[str] = None
    name__in: Optional[list[str]] = None
    type: Optional[str] = None
    type__in: Optional[list[str]] = None
    is_free: Optional[bool] = None
    is_available_in_countries__method: Annotated[
        Optional[list[str]],
        Field(alias='is_available_in_countries')
    ] = None
    total_recommendations: Annotated[Optional[int], Field(ge=0)] = None
    total_recommendations__gte: Annotated[Optional[int], Field(ge=0)] = None
    total_recommendations__lte: Annotated[Optional[int], Field(ge=0)] = None
    discount_eq__method: Annotated[Optional[int], Field(ge=0, le=100, alias='discount')] = None
    discount_gte__method: Annotated[Optional[int], Field(ge=0, le=100, alias='discount__gte')] = None
    discount_lte__method: Annotated[Optional[int], Field(ge=0, le=100, alias='discount__lte')] = None

    order_by: list[str] = ["total_recommendations"]
    search__method: Annotated[
        Optional[str],
        Field(alias='search')
    ] = None

    @staticmethod
    async def filter__is_available_in_countries(query: FindMany[FindType], value: str):
        return query.find_many(
            {f"prices.{country}.is_available": {'$eq': True} for country in value.split(',')}
        )

    @staticmethod
    async def filter__discount_eq(query: FindMany[FindType], value: int):
        return query.find_many(
            {f"prices.{settings.MAIN_COUNTRY}.price_story.0.discount": {'$eq': value}}
        )

    @staticmethod
    async def filter__discount_gte(query: FindMany[FindType], value: int):
        return query.find_many(
            {f"prices.{settings.MAIN_COUNTRY}.price_story.0.discount": {'$gte': value}}
        )

    @staticmethod
    async def filter__discount_lte(query: FindMany[FindType], value: int):
        return query.find_many(
            {f"prices.{settings.MAIN_COUNTRY}.price_story.0.discount": {'$lte': value}}
        )

    @staticmethod
    async def sort__discount(query: FindMany[FindType], direction: SortDirection):
        return query.sort((f"prices.{settings.MAIN_COUNTRY}.price_story.0.discount", direction))

    @staticmethod
    async def filter__search(query: FindMany[FindType], value: str):
        app_ids = await Index.fulltext_search(value)
        return query.find_many({"_id": {"$in": app_ids}})

    class Constants(Filter.Constants):
        model = App
        custom_ordering_fields = ("discount", )

    class Config:
        allow_population_by_field_name = True
        extra = 'allow'
