from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import Field

from app.models import App
from app.api.schemas import AppSchema, AppEditingSchema


router = APIRouter(prefix='/apps')


async def raise_if_app_already_exists(app_id: int):
    existing_app = await App.find_one(App.id == app_id)

    if existing_app is not None:
        raise HTTPException(status_code=409, detail=f'App with id {app_id} already exists')


@router.get('', response_model=list[AppSchema])
async def list_apps():
    return await App.find().to_list()


@router.get('/{app_id}', response_model=AppSchema)
async def get_app(app_id: Annotated[int, Field(gt=0)]):
    app = await App.find_one(App.id == app_id)

    if app is None:
        raise HTTPException(status_code=404, detail=f'App with id {app_id} not found')

    return app


@router.delete('/{app_id}', status_code=204)
async def delete_app(app_id: Annotated[int, Field(gt=0)]):
    app = await App.find_one(App.id == app_id)

    if app is None:
        raise HTTPException(status_code=404, detail=f'App with id {app_id} not found')

    await app.delete()  # type: ignore


@router.post('', status_code=201, response_model=AppSchema)
async def create_app(app_data: AppSchema):
    await raise_if_app_already_exists(app_data.id)
    return await App(**app_data.model_dump()).insert()  # type: ignore


@router.patch('/{app_id}', response_model=AppSchema)
async def patch_app(app_id: Annotated[int, Field(gt=0)], app_data: AppEditingSchema):
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
async def put_in_app(app_id: Annotated[int, Field(gt=0)], app_data: AppEditingSchema):
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
