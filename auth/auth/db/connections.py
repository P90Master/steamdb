from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from auth.config import settings


engine = create_async_engine(settings.DB_URL)
Session = async_sessionmaker(bind=engine)
