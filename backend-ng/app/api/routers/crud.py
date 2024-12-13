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

    new_app = App(**app_data.model_dump())
    await new_app.insert()  # type: ignore
    return new_app


@router.patch('/{app_id}', response_model=AppSchema)
async def update_app(app_id: Annotated[int, Field(gt=0)], app_data: AppEditingSchema):
    app = await App.find_one(App.id == app_id)

    if app is None:
        raise HTTPException(status_code=404, detail=f'App with id {app_id} not found')

    await app.update({"$set": app_data.model_dump(exclude_unset=True)})
    return app
