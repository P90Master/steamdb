from datetime import datetime, UTC
from typing import Annotated

from pydantic import Field, BaseModel, field_validator
from beanie import Indexed, after_event, Replace, Update, SaveChanges, Delete

from app.utils import timezone
from app.utils.cache import CacheManager


__all__ = (
    'App',
    'AppInCountry',
    'AppPrice',
)

from app.models.utils import BaseDocument


class AppPrice(BaseModel):
    timestamp: datetime | None = None
    price: Annotated[float, Field(gt=-0.01)] | None = None
    discount: Annotated[int, Field(gt=-1, lt=100, default=0)] | None = None

    @field_validator('timestamp', mode='after')
    @classmethod
    def convert_utc_to_local(cls, v):
        if v.tzinfo is None or v.tzinfo.utcoffset(v) == UTC.utcoffset(v):
            v = v.astimezone(timezone)

        return v


class AppInCountry(BaseModel):
    is_available: Annotated[bool, Field(default=True)]
    currency: Annotated[str, Field(max_length=3)] | None = None
    price_story: list[AppPrice] | None = None


class App(BaseDocument):
    class Settings:
        name = 'apps'

    id: Annotated[int, Indexed]
    name: Annotated[str, Indexed]
    type: str | None = None  # TODO: Literal['game', 'trailer', 'dlc', ...]
    short_description: str | None = None
    is_free: bool | None = None
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

    @after_event(Replace, Update, SaveChanges, Delete)
    async def reset_cache(self):
        cache_key = f'app_{self.id}'
        await CacheManager.clear(cache_key)
