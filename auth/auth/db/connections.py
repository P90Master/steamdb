from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from auth.core.config import settings


engine = create_async_engine(settings.DB_URL)
Session = async_sessionmaker(bind=engine)


async def get_db() -> AsyncSession:
    async with Session() as session:
        yield session
