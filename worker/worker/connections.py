import pika

from worker.api import SteamAPIClient, AsyncBackendAPIClient


orchestrator_connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='orchestrator-worker-broker',
        port=5672,
        credentials=pika.PlainCredentials('user', 'password')
    )
)

backend_api_client = AsyncBackendAPIClient(token=None)
steam_api_client = SteamAPIClient(token=None)
