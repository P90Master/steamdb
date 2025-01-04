import asyncio

from sqlalchemy import func, select, or_, delete

from auth.core.logger import get_logger
from auth.core.config import settings
from auth.db import Session
from auth.models import AdminToken, AccessToken, RefreshToken
from auth.celery.worker import app


logger = get_logger(settings, name='auth.scheduled_task')


async def remove_all_expired_tokens() -> int:
    async def remove_expired_admin_tokens() -> int:
        async with Session() as session:
            conditions = or_(AdminToken.expires_at < func.now(), AdminToken.is_active == False)
            delete_query = delete(AdminToken).where(conditions)
            count_query = select(func.count()).select_from(AdminToken).where(conditions)

            amount_of_expired_tokens = (await session.execute(count_query)).scalar()
            await session.execute(delete_query)
            await session.commit()
            return amount_of_expired_tokens

    async def expired_access_tokens_generator() -> int:
        async with Session() as session:
            conditions = or_(AccessToken.expires_at < func.now(), AccessToken.is_active == False)
            delete_query = delete(AccessToken).where(conditions)
            count_query = select(func.count()).select_from(AccessToken).where(conditions)

            amount_of_expired_tokens = (await session.execute(count_query)).scalar()
            await session.execute(delete_query)
            await session.commit()
            return amount_of_expired_tokens

    async def expired_refresh_tokens_generator() -> int:
        async with Session() as session:
            conditions = or_(RefreshToken.expires_at < func.now(), RefreshToken.is_active == False)
            delete_query = delete(RefreshToken).where(conditions)
            count_query = select(func.count()).select_from(RefreshToken).where(conditions)

            amount_of_expired_tokens = (await session.execute(count_query)).scalar()
            await session.execute(delete_query)
            await session.commit()
            return amount_of_expired_tokens

    return sum(
        await asyncio.gather(
            remove_expired_admin_tokens(),
            expired_access_tokens_generator(),
            expired_refresh_tokens_generator()
        )
    )


@app.task(time_limit=settings.CELERY_TASK_TIME_LIMIT)
def clean_expired_tokens():
    logger.info('Starting task to cleanup expired and inactive tokens.')

    try:
        amount_of_deleted_tokens = asyncio.run(remove_all_expired_tokens())
    except Exception as unhandled_error:
        error_msg = f'Task "clean_expired_tokens" execution failed with error: {unhandled_error}'
        logger.error(error_msg)
    else:
        logger.info(f'Cleanup task completed: {amount_of_deleted_tokens} tokens were deleted.')
