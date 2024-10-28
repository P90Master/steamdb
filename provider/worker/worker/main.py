import asyncio


async def main():
    from worker.tasks import update_app_data_task, batch_update_apps_data_task

    # result = await update_app_data_task(app_id=588650, country_code='RU')
    # print(result)

    result = await batch_update_apps_data_task(batch_of_app_ids=(945360, 570, 292030), country_code='RU')
    print("Completed")

    await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
