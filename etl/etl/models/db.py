from dataclasses import dataclass
from datetime import datetime


@dataclass
class AppPrice:
    timestamp: datetime | None = None
    price: float | None = None
    discount: int | None = None


@dataclass
class AppInCountry:
    is_available: bool = True
    currency: str | None = None
    price_story: list[AppPrice] | None = None


class App:
    id: int
    name: str
    type: str | None = None
    short_description: str | None = None
    is_free: bool | None = None
    developers: list[str] | None = None
    publishers: list[str] | None = None
    total_recommendations: int | None = None
    prices: dict[str, AppInCountry] | None = None
