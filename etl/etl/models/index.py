from dataclasses import dataclass


@dataclass
class IndexedApp:
    id: int
    name: str
    description: str | None = None
    developers: list[str] | None = None
    publishers: list[str] | None = None
