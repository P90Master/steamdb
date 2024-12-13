from datetime import datetime, UTC
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field


__all__ = (
    'AppSchema',
    'AppEditingSchema',
    'AppPriceSchema',
    'AppInCountrySchema',
)


class AppPriceSchema(BaseModel):
    timestamp: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
    price: Annotated[Decimal | None, Field(gt=-0.01, decimal_places=2)] = None
    discount: Annotated[int | None, Field(gt=-1, lt=100)] = None


class AppInCountrySchema(BaseModel):
    is_available: Annotated[bool, Field(default=True)]
    currency: Annotated[str | None, Field(max_length=3)] = None
    price_story: list[AppPriceSchema] | None = None


class AppSchema(BaseModel):
    id: int
    name: str
    type: str | None = None  # TODO: Literal['game', 'trailer', 'dlc', ...]
    short_description: str | None = None
    is_free: bool | None = None
    developers: list[str] | None = None
    publishers: list[str] | None = None
    total_recommendations: int | None = None
    prices: dict[Annotated[str, Field(max_length=2)], AppInCountrySchema] | None = None


class AppEditingSchema(BaseModel):
    name: str | None = None
    type: str | None = None
    short_description: str | None = None
    is_free: bool | None = None
    developers: list[str] | None = None
    publishers: list[str] | None = None
    total_recommendations: int | None = None
    prices: dict[Annotated[str, Field(max_length=2)], AppInCountrySchema] | None = None
