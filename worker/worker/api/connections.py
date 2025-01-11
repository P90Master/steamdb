from worker.core.config import settings

from .backend import AsyncBackendAPIClient
from .steam import SteamAPIClient


backend_api_client = AsyncBackendAPIClient(
    client_id=settings.ESSENTIAL_WORKER_CLIENT_ID,
    client_secret=settings.ESSENTIAL_WORKER_CLIENT_SECRET
)
steam_api_client = SteamAPIClient()
