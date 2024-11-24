from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime


Base = declarative_base()


class App(Base):
    __tablename__ = 'apps'

    id = Column(Integer, primary_key=True)
    last_updated = Column(DateTime, default=datetime.now)
    # TODO: Lock for parallel updating
    # is_updating = Column(Boolean, default=False)

    def __repr__(self):
        return '<App: id={}, last updated datetime is {}>'.format(
            self.id,
            self.last_updated
        )