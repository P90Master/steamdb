# Backend

Предоставляет CRUD интерфейс для взаимодействия с основной БД. Операция LIST имеет фильтрацию, сортировку, пагинацию. Фильтрация включает полнотекстовый поиск.

## Стек

- [FastAPI](https://fastapi.tiangolo.com/) - Web-фреймворк для построения API
- [MongoDB](https://www.mongodb.com/) - NoSQL документоориентированная БД - основная база проекта
- [Elasticsearch](https://www.elastic.co/) - Система поиска / Полнотекстовый индекс
- ~~[PostgreSQL](https://www.postgresql.org/) - SQL БД для Backend'a~~ Использовалась в старой версии Backend на [Django](https://www.djangoproject.com/)
- [Redis](https://redis.io/) - NoSQL key:value хранилище для кэша
- [Beanie](https://beanie-odm.dev/) - ODM для MongoDB
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Сериализация и валидация для FastAPI и [pydantic-settings](https://pydantic-docs.helpmanual.io/usage/settings/) для работы с переменными окружения
- [Aiohttp](https://aiohttp.readthedocs.io/en/stable/) - Для асинхронных HTTP-запросов к сервисам **Auth** и **Orchestrator**
- [Uvicorn](https://www.uvicorn.org/) - ASGI-сервер для FastAPI

## Как устроен

API состоит из **3** роутеров:

- `/api/v1/apps` - CRUD операции с приложениями в базе
- `/api/v1/package` - Включает один POST-эндпоинт для **worker'ов**, на который они отправляют данные об играх в фиксированном формате
- `/api/v1/tasks` - Регистрация задач для **Оркестратора** и проверка их статуса

Подробнее можно посмотреть в swagger-документации по адресу `http://127.0.0.1/docs.`

**Важно:** Операции, отличные от READ и LIST требуют аутентификации и наличия определенных прав (scopes):

- `POST /api/v1/apps` - наличие scope `backend/create`
- `PUT /api/v1/apps/{app_id}` - наличие scope `backend/update`
- `PATCH /api/v1/apps/{app_id}` - наличие scope `backend/update`
- `DELETE /api/v1/apps/{app_id}` - наличие scope `backend/delete`
- `POST /api/v1/package` - наличие scope `backend/package`
- `/api/v1/tasks` - наличие scope `backend/tasks`

Или достаточно иметь один admin-scope: `backend/*` или superuser-scope: `*` для всех выше перечисленных операций.

## Вид данных
<details>
<summary>Пример GET-запроса</summary>

```json
GET http://127.0.0.1:80/api/v1/apps/292030

{
    "id": 292030,
    "name": "The Witcher 3: Wild Hunt",
    "type": "game",
    "short_description": "You are Geralt of Rivia, mercenary monster slayer. Before you stands a war-torn, monster-infested continent you can explore at will. Your current contract? Tracking down Ciri — the Child of Prophecy, a living weapon that can alter the shape of the world.",
    "is_free": false,
    "developers": [
        "CD PROJEKT RED"
    ],
    "publishers": [
        "CD PROJEKT RED"
    ],
    "total_recommendations": 758046,
    "prices": {
        "US": {
            "is_available": true,
            "currency": "USD",
            "price_story": {
                "results": [
                    {
                        "timestamp": "2025-02-04T19:57:39.394000+03:00",
                        "price": 39.99,
                        "discount": 0
                    },
                    {
                        "timestamp": "2025-01-26T23:37:43.621000+03:00",
                        "price": 7.99,
                        "discount": 80
                    }
                ],
                "page": 1,
                "size": 10,
                "total": 2
            }
        }
    }
}
```
</details>

<details>
<summary>Пример LIST-запроса</summary>

```json
GET http://127.0.0.1:80/api/v1/apps?discount__lte=10&is_free=false&is_available_in_countries=RU&search=valve&size=1


    "results": [
        {
            "id": 10,
            "name": "Counter-Strike",
            "type": "game",
            "short_description": "Play the world's number 1 online action game. Engage in an incredibly realistic brand of terrorist warfare in this wildly popular team-based game. Ally with teammates to complete strategic missions. Take out enemy sites. Rescue hostages. Your role affects your team's success. Your team's success affects your role.",
            "is_free": false,
            "developers": [
                "Valve"
            ],
            "publishers": [
                "Valve"
            ],
            "total_recommendations": 157379,
            "prices": {
                "US": {
                    "is_available": true,
                    "currency": "USD",
                    "price": 9.99,
                    "discount": 0,
                    "last_updated": "2025-01-26T23:43:16.255000+03:00"
                },
                "GB": {
                    "is_available": true,
                    "currency": "GBP",
                    "price": 7.19,
                    "discount": 0,
                    "last_updated": "2025-01-26T23:43:17.765000+03:00"
                },
                "CN": {
                    "is_available": true,
                    "currency": "CNY",
                    "price": 37.0,
                    "discount": 0,
                    "last_updated": "2025-01-26T23:43:19.373000+03:00"
                },
                "RU": {
                    "is_available": true,
                    "currency": "RUB",
                    "price": 259.0,
                    "discount": 0,
                    "last_updated": "2025-01-26T23:43:20.887000+03:00"
                },
                "DE": {
                    "is_available": true,
                    "currency": "EUR",
                    "price": 8.19,
                    "discount": 0,
                    "last_updated": "2025-01-26T23:43:22.293000+03:00"
                },
                "JP": {
                    "is_available": true,
                    "currency": "JPY",
                    "price": 1010.0,
                    "discount": 0,
                    "last_updated": "2025-01-26T23:43:24.006000+03:00"
                },
                "BR": {
                    "is_available": true,
                    "currency": "BRL",
                    "price": 20.69,
                    "discount": 0,
                    "last_updated": "2025-01-26T23:43:25.511000+03:00"
                }
            }
        }
    ],
    "page": 1,
    "size": 1,
    "total": 10
}
```
</details>

## Особенности

Ниже приведены особенности реализации этого Backend'a, отличные от обычного FastAPI приложения:

## Кастомное кэширование

Используется собственный механизм кэширования `CacheManager`, по способу применения похожий на стандартный механизм кэширования в Django:

```python
from app.utils.cache import CacheManager, RedisBackend


@asynccontextmanager
async def lifespan(app_: FastAPI):
    cache_pool = ConnectionPool.from_url(url=settings.CACHE_URL)
    redis_instance = redis.Redis(connection_pool=cache_pool)
    CacheManager.init(
        RedisBackend(redis_instance),
        prefix=settings.CACHE_PREFIX,
        expire=settings.CACHE_TIMEOUT,
        logger=get_logger(settings, 'cache'),
    )

    yield

    CacheManager.reset()
    await cache_pool.disconnect()


app = FastAPI(lifespan=lifespan)


@app.get('/{id}', response_model=ItemSchema)
async def get_item(item_id: Annotated[int, Field(gt=0)]):
    cache_key = f'item_{item_id}'
    cached_app_data = await CacheManager.get(cache_key)

    if cached_app_data:
        item = Item(**cached_app_data)
        return ItemSchema(**item.model_dump())

    item = await Item.find_one(Item.id == item_id)

    if item is None:
        raise HTTPException(status_code=404, detail=f'Item with id {app_id} not found')

    await CacheManager.save(item.model_dump_json(), cache_key)
    return ItemSchema(**item.model_dump())
```

Архитектура `CacheManager` модульная и поддерживает любые реализации бэкенда (по дефолту имеется `RedisBackend`) и кодировщика (по дефолту имеется `JsonCoder`)

**Мотивация:** Имеющиеся инструменты кэширования для FastAPI в основном предоставляют только декораторы для всего эндпоинта, что не дает полного контроля над процессом кэширования.

## Кастомный механизм разграничения прав

Используется собственный механизм авторизации, похожий на Permissions из Django, созданный под конкретно текущий проект специально для работы с OAuth2.0 Scopes. 

```python
from app.auth import Permissions


app = FastAPI()


@app.post('', status_code=201, response_model=ItemSchema)
async def create_item(item_data: ItemSchema, _ = Depends(Permissions.can_create)):
    await raise_if_item_already_exists(item_data.id)
    return await Item(**app_data.model_dump()).insert()
```

Использует DI-механизм FastAPI, асбтрагируя эндпоинт от логики проверки прав.

Позволяет гибко конкатенировать права и объединять их в роли:

```python
class CanRead(IsAuthenticatedAndHasScopes):
    SCOPES = Scope.READ

class IsStaff(CanRead):
    SCOPES = (Scope.CREATE, Scope.UPDATE, Scope.DELETE)
```

Для доступа к эндпоинту с требованием наличия права `IsStaff` пользователь должен быть аутентифицирован и иметь scope `READ` и хотя бы один из scope (`CREATE`, `UPDATE`, `DELETE`).

Scopes в объект `request` добавляет кастомная `AuthMiddleware` - она достает access-токен из запроса и запрашивает данные о нем у Auth-сервера, помещая полученные scopes в объект `request.user.scopes`

**Мотивация:** Отсутствие адекватных альтернатив.

## Модифицированный `fastapi-filter`

Модификация либы [fastapi-filter](https://github.com/arthurio/fastapi-filter), дающая возможность использовать "method-фильтры", поведение которых описывается в отдельных функциях:

```python
from app.utils.filters import Filter


class AppFilter(Filter):
    name: Optional[str] = None
    type__in: Optional[list[str]] = None
    is_free: Optional[bool] = None

    order_by: list[str] = ["total_recommendations"]

    is_available_in_countries__method: Annotated[
        Optional[list[str]],
        Field(alias='is_available_in_countries')
    ] = None
    search__method: Annotated[
        Optional[str],
        Field(alias='search')
    ] = None

    @staticmethod
    async def filter__is_available_in_countries(query: FindMany[FindType], value: str):
        return query.find_many(
            {f"prices.{country}.is_available": {'$eq': True} for country in value.split(',')}
        )
    
    @staticmethod
    async def sort__discount(query: FindMany[FindType], direction: SortDirection):
        return query.sort((f"prices.{settings.MAIN_COUNTRY}.price_story.0.discount", direction))

    @staticmethod
    async def filter__search(query: FindMany[FindType], value: str):
        app_ids = await Index.fulltext_search(value)
        return query.find_many({"_id": {"$in": app_ids}})

    class Constants(Filter.Constants):
        model = App
        custom_ordering_fields = ("discount", )
```

Дает возможность реализовывать нестандартные и сложные сценарии фильтрации и сортировки, не нарушая общий интерфейс либы.

С помощью этой модификации был добавлен фильтр `search` - полнотекстовый поиск, использующий интеграцию с Elasticsearch, скрытую за интерфейсом `Index`.

## TODO:

- [ ] **Кэширование LIST запросов:** Сейчас кэшируются только DETAIL запросы. С ними все просто: при запросе приложения по ID занести его в кэш и держать там до истечения время жизни или до получения сигнала об изменении этого приложения.
Надо подумать как кэшировать LIST запросы с различными параметрами фильтрации, пагинации и сортировки, и как сбрасывать кэш, если одно из приложений в этих подборках изменилось. (Для пагинации применить прогрессивную стратегию: сначала кэшируется x2 от размера выборки, потом дополнительно x4, x8 и т.д.)
- [ ] **Раздельная пагинация истории цен для каждой из стран:** При Detail запросе по ID можно пагинироваться по истории цен, но эта пагинация будет общая для истории цен всех стран.
- [ ] **Admin-панель:** Прикрутить админ-панель, можно использовать решение из Auth-сервера, переделав его под работу с документами Beanie
