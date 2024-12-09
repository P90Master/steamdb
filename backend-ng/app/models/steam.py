from typing import Any

from beanie import Document, Indexed

from app.core.config import settings


__all__ = (
    'App',
)


class App(Document):
    class Settings:
        name = 'apps'

    id: Indexed(int)
    name: Indexed(str)
    type: str  # TODO: Literal['game', 'trailer', 'dlc', ...]
    short_description: str
    is_free: bool
    developers: list[str]
    publishers: list[str]
    total_recommendations: int
    prices: dict[str, Any]

    def __repr__(self) -> str:
        return f"<App {self.id}>"

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return self.id == other.id if isinstance(other, App) else False
