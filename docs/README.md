# SteamDB

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![python](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![build](https://github.com/P90Master/steamdb/workflows/CI/badge.svg)](https://github.com/steamdb/steamdb/actions)

_Автономная распределенная система для сбора, агрегации и хранения истории цен в Steam_

## Оглавление

- [Описание](#описание)
- [Особенности системы](#особенности-системы)
- [Структура](#структура)
- [Карта сети](#карта-сети)
- [Deploy](#deploy)
- [Нагрузочное тестирование](#нагрузочное-тестирование)
- [TODO](#todo)

## Описание

> **Дисклеймер:** Данный проект - реконструкция базового функционала существующего [сервиса](https://steamdb.info), мотивированная исключительно моим желанием воссоздать подобную систему своими собственными руками. От оригинального проекта я взял только исходную задачу и решал ее со своим собственным видением этой системы, используя инструментарий, которым я владею, без оглядки на оригинальное решение.

Платформа [Steam](https://store.steampowered.com) предоставляет довольно скудный [API](https://developer.valvesoftware.com/wiki/Steam_Web_API): для взаимодействия со списком приложений имеются только 2 опции: запросить общий список приложений и запросить данные об приложении по id в контексте указанной страны. List-запрос не принимает каких-либо фильтров и выдает список пар `(app_id, name)`, сваливая в одну кучу ПО, игры, доп.контент. Detail-запрос по id и коду страны предоставляет полную информацию о приложении в контексте выбранной страны. Контекст влияет на валюту и цену, а также на доступность этого продукта в стране в целом. Цены являются актуальными, узнать сколько стоил продукт до этого через API невозможно.

_Сервис SteamDB автономно мигрирует данные о приложениях в Steam в собственную базу, ведёт историю цен и скидок в разных странах и предоставляет более функциональный API, включающий сортировку, пагинацию, фильтрацию и полнотекстовый поиск._

### Особенности системы:

- **Автономность:** сразу после деплоя система начинает непрерывный процесс миграции (а впоследствии синхронизации) данных, не требуя присутствия пользователя. Процессом руководит **сервис-оркестратор**, взаимодествуя с **worker-сервисами** посредством брокера сообщений [RabbitMQ](https://www.rabbitmq.com/).
- **Полнотекстовый Поиск:** Отдельный сервис с **ETL-пайплайном** периодически мигрирует данные из основной базы [MongoDB](https://www.mongodb.com/) в полнотекстовый индекс [Elasticsearch](https://www.elastic.co/), который используется для полнотекстового поиска.
- **Аутентификация/Авторизация:** Взаимодействие компонентов системы друг с другом регламентировано протоколом **OAuth 2.0** (а именно **Client Credentials Flow** [RFC 6749](https://www.rfc-editor.org/rfc/rfc6749#section-1.3.4)). За аутентификацию отвечает **Auth-сервис** - он выписывает access-токены со scopes сервисам-клиентам и проверяет токены по требованию сервисов-серверов. За авторизацию отвечают сами сервисы - разграничение доступа происходит на основе связанных с access-token'ом scopes, которые предоставляет Auth-сервис при успешной проверке токена.
- **Система Логгирования:** Логи с ключевых компонентов собираются, агрегируются и индексируются в [Elasticsearch](https://www.elastic.co/). Система основана на [стеке ELK](https://www.elastic.co/elastic-stack) с использованием [Filebeat](https://www.elastic.co/products/beats/filebeat) в качестве сборщиков и [Apache Kafka](https://kafka.apache.org/) в роли потокового брокера между сборщиками и [Logstash](https://www.elastic.co/products/logstash).

## Структура

Система состоит из **6** компонентов, каждый из них включает в себя нескольких микросервисов.

**Подробно о каждом из компонентов можно почитать по гиперссылкам ниже:**

- [Worker](WORKER.md)
- [Orchestrator](ORCHESTRATOR.md)
- [Backend](BACKEND.md)
- [Full Text Search](FTSEARCH.md)
- [Auth](AUTH.md)
- [Logs](LOGS.md)

## Карта сети

<p align="center">
  <img src="https://github.com/P90Master/steamdb/blob/main/docs/img/network_map.png" alt="Network Map">
</p>

## Deploy

1. Создать `.env` файл (заведется с переменными по умолчанию):

    ```bash
    cp .env.template .env
    ```

2. Поднять docker compose:

    ```bash
    docker compose up -d
    ```

Для деплоя в dev-режиме:

```bash
docker compose -f docker-compose.ym -f docker-compose.dev.yml up -d
```

Dev-режим пробросит порты для доступа к API [Оркестратора](ORCHESTRATOR.md#api) и [Auth-сервера](AUTH.md#общие-сведения), а также поднимет GUI-сервисы для [Полнотекстового индекса](FTSEARCH.md#kibana) и [Основной БД](BACKEND.md#mongo-express).

Стандартный (демонстрационный) деплой подразумевает **single-host** режим.

Для **multi-host** деплоя нужно:
- Самостоятельно распределить docker-контейнеры по хостам
- Пробросить порты
- Указать актуальные host:port в `.env`
- Решить проблемы безопасности:
  - Разжиться сертификатом для HTTPS (TLS)
  - Настроить проксирование HTTP -> HTTPS в Nginx
  - Перевести Elasticsrearch-кластеры в `xpack.security.enabled: true`
  - Распределить сборщики логов по хостам, попутно закрыв [проблему с их безопасностью](LOGS.md#безопасность-а-точнее-ее-отсутствие) 

## Нагрузочное тестирование

Драйвтест [Backned'a](BACKEND.md) проводился с использованием 3 инстансов за балансировщиком Nginx:
- Каждый инстанс сидел за [uvicorn'ом](https://www.uvicorn.org/) c 4 воркерами и `LIMIT_CONCURRENCY=4096`
- Каждому инстансу было выделено по вплоть до 2 потоков (логических ядер) и 1 GB RAM

Тестирование проводилось с использованием [locust](https://locust.io/)

<p align="center">
  <img src="https://github.com/P90Master/steamdb/blob/main/docs/img/stresstest_cached_1.png" alt="Cached Case">
</p>

При DETAIL-запросе сервис держит до 1500 RPS без снижения времени ответа за счет кэша. После 1500 RPS время ответа начинает медленно ползти вверх, оставаясь в пределах разумного (для localhost теста) вплоть до 2000 RPS:

<p align="center">
  <img src="https://github.com/P90Master/steamdb/blob/main/docs/img/stresstest_cached_2.png" alt="Cached Case">
</p>

В случае с [некэшируемыми LIST-запросами](BACKEND.md#мысли-про-кэширование) все грустнее: сервис держит до 400 RPS, после чего время ответа начинает расти:

<p align="center">
  <img src="https://github.com/P90Master/steamdb/blob/main/docs/img/stresstest_nocache.png" alt="No Cache Case">
</p>

По достижение 1000 RPS сервис окончательно валится, отдавая 503. Так как запросы одинаковые, то MongoDB их закешировала и никаких проблем с таким RPS не испытывает.

## TODO

Локальные **TODO** каждого из компонентов: [Worker](WORKER.md#todo), [Orchestrator](ORCHESTRATOR.md#todo), [Backend](BACKEND.md#todo), [Auth](AUTH.md#todo),[Full Text Search](FTSEARCH.md#todo), [Logs](LOGS.md#todo)

- [ ] **Smoke-Тесты:** Пара интеграционных тестов для проверки работоспособности базовых пайплайнов (запрос данных об игре, например)
- [ ] **Полноценный CI на GitHub Actions:** Прогон Smoke-тестов + линтеры перед пушем в мастер
- [ ] **Frontend:** SPA на React.js
- [ ] **Сбор метрик:** Подключить Prometheus + Grafana
- [ ] **GraphQL API:** К существующему REST добавить GraphQL на [Strawberry](https://strawberry.rocks/)
- [ ] **Переехать на pipenv/poetry:** Использование lock-файлов
- [ ] **Kubernetes:** Добавить конфиг для mutli-host режима (оставив docker для single-host режима как дефолтного)