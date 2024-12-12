from datetime import datetime, UTC
from typing import Annotated

from pydantic import BaseModel, Field


__all__ = (
    'AppPackageSchema',
)


class AppPackageSchema(BaseModel):
    id: int
    name: str
    type: str | None  # TODO: Literal['game', 'trailer', 'dlc', ...]
    short_description: str | None
    is_free: bool | None
    developers: list[str] | None
    publishers: list[str] | None
    total_recommendations: int | None
    country_code: Annotated[str, Field(max_length=2)]
    is_available: Annotated[bool, Field(default=True)]
    currency: Annotated[str | None, Field(max_length=3)]
    price: Annotated[float | None, Field(gt=0, decimal_places=2)]
    discount: Annotated[int | None, Field(gt=0, lt=100)]
    timestamp: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
