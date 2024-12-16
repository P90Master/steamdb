from datetime import datetime, UTC
from typing import Annotated

from pydantic import Field, BaseModel, field_validator
from beanie import Indexed

from app.utils import timezone


__all__ = (
    'App',
    'AppInCountry',
    'AppPrice',
)

from app.models.utils import BaseDocument


class AppPrice(BaseModel):
    timestamp: datetime
    price: Annotated[float, Field(gt=-0.01)]
    discount: Annotated[int, Field(gt=-1, lt=100, default=0)]

    @field_validator('timestamp', mode='after')
    @classmethod
    def convert_utc_to_local(cls, v):
        if v.tzinfo is None or v.tzinfo.utcoffset(v) == UTC.utcoffset(v):
            v = v.astimezone(timezone)

        return v


class AppInCountry(BaseModel):
    is_available: Annotated[bool, Field(default=True)]
    currency: Annotated[str, Field(max_length=3)]
    price_story: list[AppPrice]


class App(BaseDocument):
    class Settings:
        name = 'apps'

    id: Annotated[int, Indexed]
    name: Annotated[str, Indexed]
    type: str | None = None  # TODO: Literal['game', 'trailer', 'dlc', ...]
    short_description: str | None = None
    is_free: bool
    developers: list[str] | None = None
    publishers: list[str] | None = None
    total_recommendations: int | None = None
    prices: dict[Annotated[str, Field(max_length=2)], AppInCountry] | None = None

    def __repr__(self) -> str:
        return f"<App {self.id}>"

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return self.id == other.id if isinstance(other, App) else False
