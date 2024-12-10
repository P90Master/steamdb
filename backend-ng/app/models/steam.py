from datetime import datetime, UTC
from typing import Annotated

from pydantic import Field, BaseModel
from beanie import Document, Indexed


__all__ = (
    'App',
)


class AppPrice(BaseModel):
    ts: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
    price: Annotated[float, Field(gt=0, decimal_places=2)]
    discount: Annotated[int, Field(gt=0, lt=100, default=0)]


class AppInCountry(BaseModel):
    is_available: Annotated[bool, Field(default=True)]
    currency: Annotated[str, Field(max_length=3)]
    price_story: list[AppPrice]


class App(Document):
    class Settings:
        name = 'apps'

    id: Annotated[int, Indexed]
    name: Annotated[str, Indexed]
    type: str  # TODO: Literal['game', 'trailer', 'dlc', ...]
    short_description: str
    is_free: bool
    developers: list[str]
    publishers: list[str]
    total_recommendations: int
    prices: dict[Annotated[str, Field(max_length=2)], AppPrice]

    def __repr__(self) -> str:
        return f"<App {self.id}>"

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return self.id == other.id if isinstance(other, App) else False
