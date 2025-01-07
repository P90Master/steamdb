from datetime import datetime
from typing import Annotated, Iterable

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi_filter import FilterDepends
from pydantic import Field

from app.auth import Permissions
from app.models import App
from app.utils.cache import CacheManager
from app.api.schemas import (
    AppSchema,
    AppEditingSchema,
    AppsListElementSchema,
    AppInCountryCompactSchema,
    AppInCountrySchema,
    PaginatedAppListSchema,
    PaginatedAppPriceSchema,
    AppWithPaginatedPricesSchema,
    AppInCountryWithPaginatedPricesSchema,
    AppFilter,
)

router = APIRouter(prefix='/apps')


async def raise_if_app_already_exists(app_id: int):
    existing_app = await App.find_one(App.id == app_id)

    if existing_app is not None:
        raise HTTPException(status_code=409, detail=f'App with id {app_id} already exists')


def compress_price_collection(price_collection: AppInCountrySchema) -> AppInCountryCompactSchema:
    compressed_price_collection = AppInCountryCompactSchema(
        currency=price_collection.currency,
        is_available=price_collection.is_available,
    )

    if price_collection.price_story:
        compressed_price_collection.price = price_collection.price_story[0].price
        compressed_price_collection.discount = price_collection.price_story[0].discount
        compressed_price_collection.last_updated = price_collection.price_story[0].timestamp

    return compressed_price_collection


def convert_apps_list_to_compact_format(apps_list: Iterable[App]) -> list[AppsListElementSchema]:
    compact_apps = []

    for app in apps_list:
        compact_price_collections = {}

        for country_code, price_collection in app.prices.items():
            compact_price_collections[country_code] = compress_price_collection(price_collection)

        compact_apps.append(
            AppsListElementSchema(
                id=app.id,
                name=app.name,
                type=app.type,
                short_description=app.short_description,
                is_free=app.is_free,
                developers=app.developers,
                publishers=app.publishers,
                total_recommendations=app.total_recommendations,
                prices=compact_price_collections
            )
        )

    return compact_apps


def paginate_app_prices(app: App, page: int, size: int) -> AppWithPaginatedPricesSchema:
    if app.prices is None:
        return AppWithPaginatedPricesSchema(**app.model_dump())

    paginated_price_collection = {}

    for country_code, price_collection in app.prices.items():
        offset = (page - 1) * size
        prices = price_collection.price_story
        paginated_price_collection[country_code] = AppInCountryWithPaginatedPricesSchema(
            is_available=price_collection.is_available,
            currency=price_collection.currency,
            price_story=PaginatedAppPriceSchema(
                results=prices[offset:offset + size],
                page=page,
                size=size,
                total=len(prices)
            )
        )

    paginated_app_dump = app.model_dump()
    paginated_app_dump['prices'] = paginated_price_collection
    return AppWithPaginatedPricesSchema(**paginated_app_dump)


@router.get('', response_model=PaginatedAppListSchema)
async def list_apps(
        page: int = Query(1, ge=0),
        size: int = Query(10, ge=1, le=100),
        filters: AppFilter = FilterDepends(AppFilter)
) -> PaginatedAppListSchema:
    # TODO: progressive cache strategy: firstly x2 size of sample, then additional x2, then x4, x8, ...
    # first caching for 1 and 2 pages, second for 3 and 4 (if needed), third for 5, 6, 7 and 8 pages, etc.
    apps_query = App.find()

    filtered_apps_query = filters.filter(apps_query)
    sorted_apps_query = filters.sort(filtered_apps_query)
    apps = await sorted_apps_query.to_list()

    offset = (page - 1) * size
    compact_apps = convert_apps_list_to_compact_format(apps)
    return PaginatedAppListSchema(
        results=compact_apps[offset:offset + size],
        page=page,
        size=size,
        total=len(compact_apps)
    )


@router.get('/{app_id}', response_model=AppWithPaginatedPricesSchema)
async def get_app(app_id: Annotated[int, Field(gt=0)], page: int = Query(1, ge=0), size: int = Query(10, ge=1, le=100)):
    # FIXME: common pagination for all countries
    # TODO: get concrete country param (by default - all)

    cache_key = f'app_{app_id}'
    cached_app_data = await CacheManager.get(cache_key)

    if cached_app_data:
        app = App(**cached_app_data)
        return paginate_app_prices(app, page, size)

    app = await App.find_one(App.id == app_id)

    if app is None:
        raise HTTPException(status_code=404, detail=f'App with id {app_id} not found')

    await CacheManager.save(app.model_dump_json(), cache_key)
    return paginate_app_prices(app, page, size)


@router.delete('/{app_id}', status_code=204)
async def delete_app(app_id: Annotated[int, Field(gt=0)], _ = Depends(Permissions.can_delete)):
    app = await App.find_one(App.id == app_id)

    if app is None:
        raise HTTPException(status_code=404, detail=f'App with id {app_id} not found')

    await app.delete()  # type: ignore


@router.post('', status_code=201, response_model=AppSchema)
async def create_app(app_data: AppSchema, _ = Depends(Permissions.can_create)):
    await raise_if_app_already_exists(app_data.id)
    return await App(**app_data.model_dump()).insert()  # type: ignore


@router.patch('/{app_id}', response_model=AppSchema)
async def patch_app(
        app_id: Annotated[int, Field(gt=0)],
        app_data: AppEditingSchema,
        _ = Depends(Permissions.can_update)
):
    app = await App.find_one(App.id == app_id)

    if app is None:
        raise HTTPException(status_code=404, detail=f'App with id {app_id} not found')

    if app_data.prices is None:
        return await app.update({'$set': app_data.model_dump(exclude_unset=True)})

    for country_code, price_collection in app_data.prices.items():
        if new_price_story_points := price_collection.price_story:
            new_price_story_points.sort(
                key=lambda story_point: datetime.fromisoformat(story_point.timestamp)
                if isinstance(story_point.timestamp, str) else story_point.timestamp,
                reverse=True
            )

        if not (existed_price_collection := app.prices.get(country_code)):
            app.prices[country_code] = price_collection
            continue

        existed_price_collection.is_available = price_collection.is_available \
            if price_collection.is_available != existed_price_collection.is_available else existed_price_collection.is_available
        existed_price_collection.currency = price_collection.currency or existed_price_collection.currency

        if not (current_price_story := existed_price_collection.price_story):
            existed_price_collection.price_story = new_price_story_points
            continue

        current_price_story.extend(new_price_story_points)
        current_price_story.sort(
            key=lambda story_point: datetime.fromisoformat(story_point.timestamp)
                    if isinstance(story_point.timestamp, str) else story_point.timestamp,
            reverse=True
        )

    app.name = app_data.name or app.name
    app.type = app_data.type or app.type
    app.short_description = app_data.short_description or app.short_description
    app.is_free = app_data.is_free if app_data.is_free != app.is_free else app.is_free
    app.developers = app_data.developers or app.developers
    app.publishers = app_data.publishers or app.publishers
    app.total_recommendations = app_data.total_recommendations or app.total_recommendations
    return await app.save()


@router.put('/{app_id}', response_model=AppSchema)
async def put_in_app(
        app_id: Annotated[int, Field(gt=0)],
        app_data: AppEditingSchema,
        _ = Depends(Permissions.can_update)
):
    app = await App.find_one(App.id == app_id)

    if app is None:
        raise HTTPException(status_code=404, detail=f'App with id {app_id} not found')

    if app_data.prices is None:
        return await app.update({'$set': app_data.model_dump(exclude_unset=True)})

    for country_code, price_collection in app_data.prices.items():
        if not (existed_price_collection := app.prices.get(country_code)):
            app.prices[country_code] = price_collection
            continue

        existed_price_collection.is_available = price_collection.is_available \
            if price_collection.is_available != existed_price_collection.is_available else existed_price_collection.is_available
        existed_price_collection.currency = price_collection.currency or existed_price_collection.currency

        if not (price_story := price_collection.price_story):
            continue

        price_story.sort(
            key=lambda story_point: datetime.fromisoformat(story_point.timestamp)
                    if isinstance(story_point.timestamp, str) else story_point.timestamp,
            reverse=True
        )
        existed_price_collection.price_story = price_story

    app.name = app_data.name or app.name
    app.type = app_data.type or app.type
    app.short_description = app_data.short_description or app.short_description
    app.is_free = app_data.is_free if app_data.is_free != app.is_free else app.is_free
    app.developers = app_data.developers or app.developers
    app.publishers = app_data.publishers or app.publishers
    app.total_recommendations = app_data.total_recommendations or app.total_recommendations

    return await app.save()
