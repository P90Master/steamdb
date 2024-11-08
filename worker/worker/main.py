from worker.messenger import orchestrator_channel
from worker.logger import logger


def main():
    '''
    from worker.tasks import update_app_data_task, batch_update_apps_data_task

    while True:
        result = await batch_update_apps_data_task(batch_of_app_ids=(945360, 570, 292030), country_code='RU')
        print("Completed")

        # result = await update_app_data_task(app_id=588650, country_code='RU')
        # print(result)

        await asyncio.sleep(20)
    '''
    try:
        orchestrator_channel.start_consuming()

    except Exception as critical_error:
        logger.critical(f"An unhandled exception received. Exception: {critical_error}")
        return


if __name__ == '__main__':
    main()
