from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.utils import timezone


__all__ = (
    'AppPackageSchema',
    'AppPackageDataSchema',
)


class AppPackageDataSchema(BaseModel):
    id: int
    name: str | None = None
    updated_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(timezone))]
    type: str | None = None  # TODO: Literal['game', 'trailer', 'dlc', ...]
    short_description: str | None = None
    is_free: bool | None = None
    developers: list[str] | None = None
    publishers: list[str] | None = None
    total_recommendations: int | None = None
    country_code: Annotated[str, Field(max_length=2)]
    is_available: Annotated[bool, Field(default=True)]
    currency: Annotated[str | None, Field(max_length=3, default=None)]
    price: Annotated[float | None, Field(gt=-0.01, default=None)]
    discount: Annotated[int | None, Field(gt=-1, lt=100, default=None)]
    timestamp: Annotated[datetime, Field(default_factory=lambda: datetime.now(timezone))]

    @field_validator('price', mode='after')
    @classmethod
    def round_price(cls, v):
        if isinstance(v, float):
            return round(v, 2)

        return v

    @model_validator(mode='after')
    def set_is_free(self) -> Self:
        if self.is_free is not None:
            return self

        if self.price is None:
            return self

        self.is_free = True if self.price == 0.0 else False
        return self

    @field_validator('timestamp', mode='after')
    @classmethod
    def ensure_aware_timestamp(cls, v):
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone)

        return v


class AppPackageSchema(BaseModel):
    data: AppPackageDataSchema
    is_success: bool
