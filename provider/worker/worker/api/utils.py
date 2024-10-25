import asyncio
import aiohttp


class SessionManagerException(Exception):
    pass


class SessionManager:
    """
    Creates a session and ensures that it does not close prematurely.
    """

    def __init__(self, *session_args, **session_kwargs):
        self._readers = 0
        self._session = None
        self._lock = asyncio.Lock()
        self._session_args = session_args
        self._session_kwargs = session_kwargs

    async def __aenter__(self):
        async with self._lock:
            self._readers += 1

            if self._readers == 1:
                self._session = aiohttp.ClientSession(*self._session_args, **self._session_kwargs)
                return self._session

            if self._session is None:
                raise SessionManagerException('Session has readers, but has not been initialized')

            return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async with self._lock:
            self._readers -= 1

            if self._readers == 0:
                await self._session.close()
                self._session = None

            return False
