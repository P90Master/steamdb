from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from app.utils import timezone


__all__ = (
    'AppSchema',
    'AppEditingSchema',
    'AppPriceSchema',
    'AppInCountrySchema',
    'AppsListElementSchema',
    'AppInCountryCompactSchema',
)


class AppPriceSchema(BaseModel):
    timestamp: Annotated[datetime, Field(default_factory=lambda: datetime.now(timezone))]
    price: Annotated[float | None, Field(gt=-0.01)] = None
    discount: Annotated[int | None, Field(gt=-1, lt=100)] = None

    @field_validator('timestamp', mode='after')
    @classmethod
    def ensure_aware_timestamp(cls, v):
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone)

        return v

    @field_validator('price', mode='after')
    @classmethod
    def round_price(cls, v):
        if isinstance(v, float):
            return round(v, 2)

        return v


class AppInCountrySchema(BaseModel):
    is_available: Annotated[bool, Field(default=True)]
    currency: Annotated[str | None, Field(max_length=3)] = None
    price_story: Annotated[list[AppPriceSchema] | None, Field(default_factory=list)]


class AppInCountryCompactSchema(BaseModel):
    is_available: Annotated[bool, Field(default=True)]
    currency: Annotated[str | None, Field(max_length=3)] = None
    price: Annotated[float | None, Field(gt=-0.01)] = None
    discount: Annotated[int | None, Field(gt=-1, lt=100)] = None
    last_updated: datetime | None = None


class AppSchema(BaseModel):
    id: int
    name: str | None = None
    type: str | None = None  # TODO: Literal['game', 'trailer', 'dlc', ...]
    short_description: str | None = None
    is_free: bool | None = None
    developers: list[str] | None = None
    publishers: list[str] | None = None
    total_recommendations: int | None = None
    prices: dict[Annotated[str, Field(max_length=2)], AppInCountrySchema] | None = None


class AppsListElementSchema(BaseModel):
    id: int
    name: str | None = None
    type: str | None = None
    short_description: str | None = None
    is_free: bool | None = None
    developers: list[str] | None = None
    publishers: list[str] | None = None
    total_recommendations: int | None = None
    prices: dict[Annotated[str, Field(max_length=2)], AppInCountryCompactSchema] | None = None


class AppEditingSchema(BaseModel):
    name: str | None = None
    type: str | None = None
    short_description: str | None = None
    is_free: bool | None = None
    developers: list[str] | None = None
    publishers: list[str] | None = None
    total_recommendations: int | None = None
    prices: dict[Annotated[str, Field(max_length=2)], AppInCountrySchema] | None = None
