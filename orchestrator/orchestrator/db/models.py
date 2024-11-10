from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime


Base = declarative_base()


class App(Base):
    __tablename__ = 'apps'

    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_updating = Column(Boolean, default=False)

    def __repr__(self):
        return '<App: id={}, name="{}", last updated datetime is {}, is updating now - {}>'.format(
            self.id,
            self.name,
            self.last_updated,
            self.is_updating
        )