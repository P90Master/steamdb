# Full Text Search

Сервис непрерывной идексации данных из основной базы в полнотекстовом индексе [Elasticsearch](https://www.elastic.co/). Используется для реализации полнотекстового поиска в Backend.

## Стек

- [Elasticsearch](https://www.elastic.co/) - полнотекстовый индекс
- [Redis](https://redis.io/) - хранилище состояния ETL процесса & очередь для ETL
- [Pymongo](https://pymongo.readthedocs.io/en/stable/) - биндинг для работы с основной базой [MongoDB](https://www.mongodb.com/)
- [Pydantic](https://pydantic-docs.helpmanual.io/) - дочерняя либа [pydantic-settings](https://pydantic-docs.helpmanual.io/usage/settings/) для работы с переменными окружения

## Как устроен

Состоит из **4** сервисов:

- ETL-пайплайн: Основной сервис. Разбит на 3 физических процесса: **Extract > Transform > Load**, взаимодействующих друг с другом посредством очередей.
- Хранилище состояния ETL процессов (f.e. Transform запущен или нет - чтобы избежать параллельной работы).
- Внешняя очередь для ETL процессов.
- Полнотекстовый индекс, куда помещаются данные, и к которому обращается Backend в рамках полнотекстового поиска.

## ETL

Состоит из 2 основных процессов: **Extract*** и **Load**. **Extract*** разбит на 2 подпроцесса: **Extract** и **Transform** с помощью `multiprocessing`,
в качестве очереди между ними используется `InMemoryQueue` с бекендом shared-memory `multiprocessing.Queue`. Такое решение обусловлено тем, что процесс **Transform** довольно примитивен,
а использование внешней очереди только вызовет накладные расходы на передачу по сети.

Однако это легко изменить, т.к. pipeline-компоненты работают с абстрактным интерфейсом очередей `(input_queue: AbstractQueue, output_queue: AbstractQueue)` - достаточно подменить `InMemoryQueue` на `RedisQueue` с бекендом `redis`.

В **Transform > Load** уже используется внешняя очередь `RedisQueue`.

Роль каждого компонента:

- **Extract** - Батчами достает из основной БД новые (или обновленные) данные и пушит их в очередь **Transform**.
- **Transform** - Пуллит данные из своей очереди, приводит их к виду, в каком они будут храниться в индексе и пушит в очередь **Load**.
- **Load** - Пуллит данные из своей очереди и помещает их в индекс.

## Схема

<p align="center">
  <img src="https://github.com/P90Master/steamdb/blob/main/docs/img/etl.png" alt="ETL Pipeline">
</p>

## Концепция компонентов

Каждый компонент внешнего пайплайна содержит в себе внутренний пайплайн, состоящий из функций-корутин (не путать с `async.Coroutine`) - генераторов, объединенных в цепочку последовательных вызовов с передачей промежуточных данных через `.send()`.

Концептуальный пример такого пайплайна:

```python
def coroutine(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        fn = func(*args, **kwargs)
        next(fn)
        return fn

    return wrapper

def pull(input_queue: AbstractQueue, next_step: callable, stop_signal_: threading.Event):
    while not stop_signal_.is_set():
        try:
            raw_data = input_queue.get(timeout=1)  # to prevent thread lock
        except Empty:
            continue
        next_step.send(raw_data)

@coroutine
def transform(next_step: callable):
    while True:
        data: Any = (yield)
        # Do something with data
        next_step.send(data)

@coroutine
def push(output_queue: AbstractQueue):
    while True:
        data: Any = (yield)
        output_queue.put(data)

input, output = InMemoryQueue(), InMemoryQueue()
pusher = push(queue)
serializer = serialize(pusher)
stop_signal = threading.Event()
pipeline = threading.Thread(target=pull, args=(input_queue, serializer, stop_signal))

pipeline.start()
time.sleep(10)

stop_signal.set()
pipeline.join()
```

## TODO:

- [ ] **Разнести StateStorage и ExternalQueue по разным инстансам Redis:** Сейчас один экземпляр Redis используется для внешней очереди и StateStorage
- [ ] **Возврат в очередь при неудаче:** В **Load** при пуше в индекс если происходит фейл, то процесс будет бесконечно пытаться запушить, пока ему это не удастся (см. `@backoff` [тут](https://github.com/P90Master/steamdb/blob/main/etl/etl/utils/decorators.py#L31)). Однако если процесс умрет, то батч данных, спулленый из очереди будет утерен. Предыдущие компоненты будут думать, что они успешно обработали эту часть данных => эти данные не попадут в индекс, пока они снова не будут обновлены на стороне основной БД.
