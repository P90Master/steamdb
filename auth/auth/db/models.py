from datetime import datetime
from typing import Annotated

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, declared_attr, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs


__all__ = ["Base", "int_pk", "str_pk", "str_unique", "last_updated"]


int_pk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
str_pk = Annotated[str, mapped_column(primary_key=True)]
str_unique = Annotated[str, mapped_column(unique=True, nullable=False)]
last_updated = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)]


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"
