from worker.setting import settings
from worker.api import backend_api_client, steam_api_client

from .connections import orchestrator_channel
from .tasks import TaskManager
from .utils import HandledException


def main():
    logger = settings.LOGGER

    task_manager = TaskManager(
        messenger_channel=orchestrator_channel,
        backend_api_client=backend_api_client,
        steam_api_client=steam_api_client,
        logger=logger
    )

    def handle_income_task(ch, method, properties, body):
        task_manager.handle_received_task_message(ch, method, properties, body)

    orchestrator_channel.basic_consume(queue=settings.RABBITMQ_INCOME_QUERY, on_message_callback=handle_income_task)

    while True:
        try:
            orchestrator_channel.start_consuming()

        except HandledException:
            continue

        except Exception as unhandled_critical_error:
            logger.critical(f"An unhandled exception received. Exception: {unhandled_critical_error}")
            return


if __name__ == '__main__':
    main()
