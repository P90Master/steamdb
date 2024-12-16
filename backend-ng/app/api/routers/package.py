from datetime import datetime

from fastapi import APIRouter

from app.models import App
from app.api.schemas import AppPackageSchema, AppPackageDataSchema, AppInCountrySchema, AppPriceSchema, AppSchema


router = APIRouter(prefix='/package')


async def build_new_price_collection(package: AppPackageDataSchema) -> AppInCountrySchema:
    if is_available := package.is_available:
        # TODO: handle validation errors
        new_price_story_point = AppPriceSchema(
            timestamp=package.timestamp,
            price=package.price,
            discount=package.discount
        )
        new_price_collection = AppInCountrySchema(
            is_available=is_available,
            currency=package.currency,
            price_story=[new_price_story_point]
        )

    else:
        new_price_collection = AppInCountrySchema(
            is_available=is_available,
        )

    return new_price_collection


async def build_new_app_data(package: AppPackageDataSchema) -> AppSchema:
    new_price_collection = await build_new_price_collection(package)
    return AppSchema(
        id=package.id,
        name=package.name,
        type=package.type,
        short_description=package.short_description,
        is_free=package.is_free,
        developers=package.developers,
        publishers=package.publishers,
        total_recommendations=package.total_recommendations,
        prices={package.country_code: new_price_collection}
    )


async def extract_common_app_fields_from_package_into_app(app: AppSchema, package: AppPackageDataSchema) -> AppSchema:
    app.name = package.name or app.name
    app.type = package.type or app.type
    app.short_description = package.short_description or app.short_description
    app.is_free = package.is_free if package.is_free != app.is_free else app.is_free
    app.developers = package.developers or app.developers
    app.publishers = package.publishers or app.publishers
    app.total_recommendations = package.total_recommendations or app.total_recommendations
    return app


def add_price_story_point_to_price_collection(
        price_collection: AppInCountrySchema,
        package: AppPackageDataSchema
) -> AppInCountrySchema:
    def add_new_price_story_point():
        new_price_story_point = AppPriceSchema(
            timestamp=package.timestamp,
            price=package.price,
            discount=package.discount
        )
        price_collection.price_story.append(new_price_story_point)
        price_collection.price_story.sort(
            key=lambda price_story: datetime.fromisoformat(price_story.timestamp)
                    if isinstance(price_story.timestamp, str) else price_story.timestamp,
            reverse=True
        )

    if not price_collection.price_story:
        add_new_price_story_point()
        return price_collection

    last_price_story_point = price_collection.price_story[0]
    if last_price_story_point.price != package.price or last_price_story_point.discount != package.discount:
        add_new_price_story_point()

    return price_collection


async def update_existed_price_collection(app: AppSchema, package: AppPackageDataSchema) -> AppInCountrySchema:
    price_collection = app.prices.get(package.country_code, AppInCountrySchema())

    price_collection.currency = package.currency or price_collection.currency
    price_collection.is_available = package.is_available \
        if package.is_available != price_collection.is_available else price_collection.is_available
    price_collection = add_price_story_point_to_price_collection(price_collection, package)

    return price_collection


async def update_app(app: AppSchema, package: AppPackageDataSchema) -> AppSchema:
    if package.is_available:
        app = await extract_common_app_fields_from_package_into_app(app, package)

    if package.country_code not in app.prices:
        app.prices[package.country_code] = await build_new_price_collection(package)

    else:
        app.prices[package.country_code] = await update_existed_price_collection(app, package)

    return await app.update({'$set': app.model_dump(exclude_unset=True)})


async def handle_failed_package(package: AppPackageDataSchema) -> AppSchema:
    app = await App.find_one(App.id == package.id)

    if app is None:
        return AppSchema(id=package.id)

    package.is_available = False
    return await update_app(app, package)


async def handle_successful_package(package: AppPackageDataSchema) -> AppSchema:
    app = await App.find_one(App.id == package.id)
    package.is_available = True

    if app is None:
        new_app_data = await build_new_app_data(package)
        return await App(**new_app_data.model_dump()).insert()  # type: ignore

    return await update_app(app, package)


@router.post('', status_code=201)
async def handle_app_package(package: AppPackageSchema):
    if package.is_success:
        await handle_successful_package(package.data)

    else:
        await handle_failed_package(package.data)
