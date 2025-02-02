# Auth Server

Сервис, отвечающий за аутентификацию других сервисов в системе SteamDB. Выдает access и refresh токены для сервисов и предоставляет о них информацию. Работает по стандарту **OAuth 2.0 Client Credentials Flow** [RFC 6749](https://www.rfc-editor.org/rfc/rfc6749#section-1.3.4).

## Стек

- [PostgreSQL](https://www.postgresql.org/) - БД для хранения токенов, клиентов, ролей и т.д.
- [Redis](https://redis.io/) - NoSQL key:value хранилище для кэша & брокер сообщений для Celery
- [FastAPI](https://fastapi.tiangolo.com/) - Web-фреймворк для построения API
- [Celery](https://docs.celeryq.dev/en/stable/) - фреймворк для асинхронного выполнения задач / асинхронная очередь задач
- [Celery Beat](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html) - планировщик задач для Celery
- [SQLAlchemy 2.0](https://www.sqlalchemy.org/) - ORM с поддержкой асинхронной работы
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Сериализация и валидация для FastAPI и [pydantic-settings](https://pydantic-docs.helpmanual.io/usage/settings/) для работы с переменными окружения
- [Uvicorn](https://www.uvicorn.org/) - ASGI-сервер для API

## Общие сведения

Весь API состоит из **3** эндпоинтов:

- `/api/v1/token` - Обменивает credentials клиента на access и refresh токены
- `/api/v1/introspect` - Проверяет access-токен на валидность. В случае успешной проверки возвращает id клиента и scopes, которые привязаны к этому токену
- `/api/v1/token_refresh` - Принимает refresh токен, возвращая новый access-токен

Подробнее можно посмотреть в swagger-документации по адресу `http://127.0.0.1/docs.`

**Важно:** API Auth-сервера считается внутренним и недоступен извне при стандартном деплое (см. пункт [Deploy](README.md#Deploy)).

Имеется **Admin-панель** по адресу `http://127.0.0.1:5000/admin/`, доступная извне. В панели можно управлять клиентами, токенами, разрешениями и объединять их в роли:

<p align="center">
  <b>Управление токенами</b>
  <img src="https://github.com/P90Master/steamdb/blob/main/docs/img/auth_admin_tokens.png" alt="Admin Panel Tokens">
</p>

<p align="center">
  <b>Управление клиентами</b>
  <img src="https://github.com/P90Master/steamdb/blob/main/docs/img/auth_admin_clients.png" alt="Admin Panel Clients">
</p>

<p align="center">
  <b>Управление Разрешениями</b>
  <img src="https://github.com/P90Master/steamdb/blob/main/docs/img/auth_admin_scopes.png" alt="Admin Panel Scopes">
</p>

<p align="center">
  <b>Управление Ролями</b>
  <img src="https://github.com/P90Master/steamdb/blob/main/docs/img/auth_admin_roles.png" alt="Admin Panel Roles">
</p>

Доступ к панели по кредам, указанными в `AUTH_SUPERUSER_USERNAME` и `AUTH_SUPERUSER_PASSWORD`. Superuser может создавать других пользователей-администраторов:

<p align="center">
  <b>Управление Пользователями</b>
  <img src="https://github.com/P90Master/steamdb/blob/main/docs/img/auth_admin_users.png" alt="Admin Panel Users">
</p>

## Алгоритм Аутентификации

Демонстрация на примере визуализации алгоритма отправки worker'ом пакета с данными об приложении в Backend:

<p align="center">
  <img src="https://github.com/P90Master/steamdb/blob/main/docs/img/auth_worker_algorithm.png" alt="Worker->Backend pipeline">
</p>

## Кэширование

Результаты работы эндпоинта `/api/v1/introspect` кэшируются на стороне Auth Сервера, с применением кастомного `Cache Manager`, [используемого](BACKEND.md#кастомное-кэширование) в Backend.
Ключем кэша является access-токен.

Конечно, эффективней было бы кэшировать данные о токене на стороне самого Backend'a (или любого другого сервиса-потребителя), но хранить данные о токене и сам токен (пусть даже в хэше) на стороне **небезопасно**.

## Очистка expired токенов

Устаревшие токены очищаются в рамках периодической Celery-таски.

## TODO:

- [ ] **Throttle-механизм для /token:** Сейчас клиент может бесконечно создавать новые токены. Когда количество токенов переваливает за `MAX_ACCESS_TOKENS_PER_CLIENT`, все старые токены помечаются как неактивные, но не удаляются. Их удалением занимается периодическая Celery-таска. В перерывах между очисткой можно заспамить базу токенами. **Решение:** либо удалять токены на месте, либо ограничить количество запросов на `/token` для клиента (throttling).
- [ ] **Throttle-механизм для /token_refresh:** См. выше.
- [ ] **Коллизия токенов:** При создании токенов есть гипотетическая вероятность коллизии, от которой пока нет никаких механизмов защиты.
