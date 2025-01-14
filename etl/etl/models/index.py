from dataclasses import dataclass
from datetime import datetime


@dataclass
class IndexedApp:
    id: int
    name: str
    updated_at: datetime
    short_description: str | None = None
    developers: list[str] | None = None
    publishers: list[str] | None = None
