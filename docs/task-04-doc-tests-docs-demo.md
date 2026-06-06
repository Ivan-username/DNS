# Task 04 Doc. Автоматические тесты, документация и демонстрация

## Краткое введение

Task 04 делает проект проверяемым и готовым к сдаче. После настройки DNS-инфраструктуры важно доказать, что она работает воспроизводимо: master и slave отвечают, записи имеют ожидаемые значения, reverse DNS работает, latency приемлемый, AXFR ограничен, а документация позволяет запустить и защитить проект без дополнительного объяснения.

Ручные команды `dig` полезны для демонстрации, но автоматические тесты нужны для повторяемой проверки. В этом проекте основной стек тестов - Python, `pytest` и `dnspython`.

## Почему выбран такой способ

`pytest` выбран потому, что он дает понятные тесты и сообщения об ошибках. `dnspython` выбран потому, что умеет выполнять DNS-запросы и возвращать структурированные DNS-ответы. Это надежнее, чем разбирать текстовый вывод `dig` во всех проверках.

Bash остается полезен для AXFR и ручных сценариев, потому что zone transfer удобно показать одной командой `dig AXFR`.

Отдельная презентация пока не нужна. Для сдачи достаточно README, документов в `docs/` и демо-сценария в `docs/task-04-doc-tests-docs-demo.md` или отдельном `docs/demo-script.md`, если отдельный файл будет добавлен позже.

## Автоматические тесты

Текущее состояние перед Task 04 зависит от выполнения Task 02 и Task 03. Если DNS-инфраструктура еще не реализована, тесты и демо-сценарий нужно писать как следующий слой поверх будущих `docker-compose.yml`, `master/`, `slave/` и `tests/`. Если master/slave уже созданы, Task 04 финализирует проверяемость и документацию.

Минимальная структура:

```text
tests/
├── requirements.txt
├── test_records.py
├── test_latency.py
├── test_zone_transfer.sh
└── manual-checks.md
```

`tests/requirements.txt`:

```text
pytest
dnspython
```

Если тесты запускаются внутри `dns-client`, контейнер должен иметь Python, pip и зависимости. Если зависимости устанавливаются вручную, это нужно описать в README.

## Тесты DNS-записей

`tests/test_records.py` должен проверять:

- `web.internal A -> 10.10.0.20`;
- `web.internal AAAA -> fd00:10:10::20`;
- `internal MX -> mail.internal`;
- `internal TXT -> course=dns-project`;
- `www.internal CNAME -> web.internal`;
- reverse lookup `10.10.0.20 -> web.internal`;
- ответы master;
- ответы slave.

Тесты должны явно указывать DNS-сервер, к которому обращаются. Это помогает быстро понять, где ошибка: в master, slave, transfer зон или самих записях.

Пример логики теста:

```python
import dns.resolver

def query(server, name, record_type):
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [server]
    return resolver.resolve(name, record_type, lifetime=2)
```

Рекомендуемые адреса серверов:

- master: `10.10.0.2`;
- slave: `10.10.0.3`.

## Latency-тесты

`tests/test_latency.py` должен проверять среднее время ответа master и slave.

Рекомендуемый сценарий:

- выполнить несколько запросов к `dns-master`;
- выполнить несколько запросов к `dns-slave`;
- измерить среднее время;
- сравнить с порогом.

Рекомендуемый порог для Docker-сети - `100 ms`. Если среда нестабильная, порог можно сделать мягче, но это нужно объяснить в комментарии или README.

Важно проверять не один запрос, а несколько. Первый запрос может быть медленнее из-за запуска, кеша или сетевой инициализации.

## AXFR-тест

`tests/test_zone_transfer.sh` нужен для проверки zone transfer.

Он должен проверять:

- AXFR работает там, где должен работать;
- зона содержит ожидаемые записи;
- неавторизованный AXFR запрещен, если это можно воспроизвести в текущей compose-схеме;
- скрипт завершается с ненулевым кодом при ошибке.

Пример команд внутри скрипта:

```bash
dig @dns-master internal AXFR
dig @dns-slave web.internal A
```

Если `dns-client` не имеет права выполнять AXFR, скрипт должен проверять отказ или использовать другой способ подтвердить, что slave получил зону.

## Единый запуск тестов

В README должен быть один основной способ запуска тестов. Например:

```bash
docker compose exec dns-client pytest tests
docker compose exec dns-client bash tests/test_zone_transfer.sh
```

Если добавляется `Makefile`, основной сценарий может быть таким:

```bash
make test
```

В таком случае `make test` должен запускать и Python-тесты, и AXFR-проверку.

## Документация

Task 04 должен финализировать документацию так, чтобы проект можно было защитить без устных пояснений автора.

Текущий стиль документации в проекте - task-oriented файлы `task-XX-doc-...md`. Поэтому базовые темы можно держать внутри этих файлов, а отдельные тематические документы добавлять только если материал станет слишком большим.

Обязательные документы в текущем стиле:

- `README.md` - быстрый старт, структура, команды запуска, команды проверки, ссылки на docs;
- `docs/task-01-doc-context-architecture.md` - объяснение DNS с нуля и общая архитектура;
- `docs/task-02-doc-infrastructure-master.md` - master DNS, zones, logging и `rndc`;
- `docs/task-03-doc-slave-security.md` - slave DNS, AXFR, ACL, DNSSEC, Split-Horizon и RRL;
- `docs/task-04-doc-tests-docs-demo.md` - тесты, README и демо-сценарий.

В начале каждого документа нужно дать краткое введение в тему, затем объяснить, почему выбран текущий способ, и только потом описывать решение и команды.

## README

README должен содержать:

- краткое введение в проект;
- цель проекта;
- выбранный стек;
- почему выбран BIND9;
- почему используется Docker Compose;
- список сервисов;
- таблицу IP-адресов;
- структуру репозитория;
- быстрый старт;
- ручные команды проверки;
- команды запуска тестов;
- ссылки на документы;
- известные ограничения.

README не должен ссылаться на отдельную презентацию, потому что презентация пока не требуется.

## DNS basics в `docs/task-01-doc-context-architecture.md`

Документ нужен для человека, который не знаком с DNS.

Он должен объяснять:

- зачем нужен DNS;
- что такое домен и зона;
- что такое A, AAAA, MX, TXT, CNAME, PTR;
- что такое forward и reverse DNS;
- что такое авторитативный сервер;
- что такое рекурсивный сервер;
- зачем нужны master и slave;
- как эти понятия используются в проекте.

## BIND9 vs Unbound в документации

Документ должен объяснять:

- зачем сравнивать DNS-серверы;
- что умеет BIND9;
- что умеет Unbound;
- почему в проекте выбран BIND9;
- почему Unbound пока не реализуется;
- можно ли использовать BIND9 и Unbound вместе;
- какие пункты задания закрывает BIND9;
- какие пункты мог бы закрывать Unbound в более сложной архитектуре.

Вывод должен быть однозначным: для текущего проекта BIND9 является основной технологией, Unbound описывается как альтернатива для рекурсивного DNS.

## Demo script в `docs/task-04-doc-tests-docs-demo.md`

Демо-сценарий нужен для защиты проекта. Он должен быть пошаговым и воспроизводимым.

Рекомендуемый порядок:

1. Показать структуру репозитория.
2. Запустить `docker compose up -d --build`.
3. Показать `docker compose ps`.
4. Проверить master.
5. Проверить slave.
6. Проверить forward zone.
7. Проверить reverse zone.
8. Проверить AXFR.
9. Проверить ACL и рекурсию.
10. Проверить DNSSEC validation.
11. Показать Split-Horizon.
12. Показать logging.
13. Показать `rndc`.
14. Запустить автоматические тесты.
15. Кратко объяснить BIND9 vs Unbound.

Для каждого шага лучше указать команду и ожидаемый результат.

## Ручные команды проверки

Запуск:

```bash
docker compose up -d --build
docker compose ps
```

Проверка записей:

```bash
docker compose exec dns-client dig @dns-master web.internal A
docker compose exec dns-client dig @dns-master web.internal AAAA
docker compose exec dns-client dig @dns-master internal MX
docker compose exec dns-client dig @dns-master internal TXT
docker compose exec dns-client dig @dns-master www.internal CNAME
docker compose exec dns-client dig @dns-master -x 10.10.0.20
docker compose exec dns-client dig @dns-slave web.internal A
```

Запуск тестов:

```bash
docker compose exec dns-client pytest tests
docker compose exec dns-client bash tests/test_zone_transfer.sh
```

## Критерии готовности Task 04

- Есть `tests/requirements.txt`.
- Есть тесты A, AAAA, MX, TXT, CNAME и PTR.
- Есть проверки master и slave.
- Есть latency-тест.
- Есть AXFR-тест или воспроизводимая ручная AXFR-проверка.
- Тесты запускаются одной понятной командой или двумя явно описанными командами.
- README позволяет запустить проект с нуля.
- README содержит команды ручной проверки и тестов.
- Документы объясняют DNS, BIND9 vs Unbound и демо-сценарий.
- Документация не требует отдельной презентации для защиты проекта.
