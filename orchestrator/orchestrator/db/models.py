from datetime import datetime
from typing import Annotated

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column


int_pk = Annotated[int, mapped_column(primary_key=True)]
last_updated = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)]
lock = Annotated[bool, mapped_column(default=False)]


class Base(DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"


class App(Base):
    id: Mapped[int_pk]
    last_updated: Mapped[last_updated]
    # TODO: Lock for parallel updating
    # is_updating: Mapped[lock]

    def __repr__(self):
        return f'<App: id={self.id}, last updated datetime is {self.last_updated}>'
