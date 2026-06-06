# Task 04 Doc. Автоматические тесты, документация и демонстрация

## Краткое введение

Этот этап делает DNS-инфраструктуру проверяемой и готовой к защите. Ручные
команды `dig` показывают отдельные свойства сервера, а автоматические тесты
доказывают, что записи, master/slave и задержка ответа остаются корректными при
повторном запуске.

## Почему выбран такой способ

`pytest` и `dnspython` используются потому, что работают с DNS-ответами как со
структурированными объектами: тест может проверить тип записи, значение,
авторитативный флаг и код ответа без разбора форматированного текста.

Bash оставлен для AXFR, потому что разрешенный и запрещенный zone transfer
нагляднее всего показать через `dig`. Docker Compose, `dig`, `rndc` и тесты
вместе дают короткий воспроизводимый сценарий защиты без отдельной презентации.

## Реализованное решение

Лаборатория состоит из BIND9 master, BIND9 slave, доверенного тестового клиента
и внешнего клиента. Master хранит внутреннюю и внешнюю версии зоны `internal`,
обслуживает рекурсию только для доверенной сети и валидирует DNSSEC внешних
ответов. Slave получает внутреннюю forward и reverse зоны через разрешенный
transfer. Split-Horizon возвращает разные адреса `web.internal` внутреннему и
внешнему клиенту. RRL, logging и `rndc` включены на master. Все основные записи
и средняя задержка проверяются автоматически.

## Автоматические тесты

Файлы:

| Файл | Назначение |
| --- | --- |
| `tests/test_records.py` | A, AAAA, MX, TXT, CNAME, PTR, master и slave |
| `tests/test_latency.py` | Средняя задержка master и slave |
| `tests/test_zone_transfer.sh` | Разрешенный AXFR, запрещенный AXFR и ответ slave |
| `tests/requirements.txt` | `pytest` и `dnspython` |

Latency измеряется по пяти запросам к `web.internal`. Порог по умолчанию равен
`100 ms`, что достаточно мягко для локальной Docker-сети и при этом позволяет
обнаружить явную проблему. Параметры можно изменить переменными окружения
`DNS_LATENCY_SAMPLES` и `DNS_LATENCY_MAX_MS`.

Основной запуск:

```bash
make test
```

Отдельные части:

```bash
make pytest
make axfr
```

## Демо-сценарий

### 1. Показать структуру проекта

```bash
find . -maxdepth 2 -type f -not -path './.git/*' -not -path './.ai/*' | sort
```

Объяснить, что `master/` содержит исходные зоны, `slave/` хранит конфигурацию
secondary-сервера, `tests/` содержит проверки, а `docs/` - документацию.

### 2. Запустить лабораторию

```bash
docker compose up -d --build
docker compose ps
```

Ожидаются четыре запущенных сервиса: `dns-master`, `dns-slave`, `dns-client` и
`dns-external-client`.

### 3. Проверить конфигурацию BIND и зоны

```bash
docker compose exec dns-master named-checkconf /etc/bind/named.conf
docker compose exec dns-slave named-checkconf /etc/bind/named.conf
docker compose exec dns-master named-checkzone internal /etc/bind/zones/db.internal
docker compose exec dns-master named-checkzone 0.10.10.in-addr.arpa /etc/bind/zones/db.10.10.0
```

Ожидаемый результат: команды завершаются без ошибок, `named-checkzone`
показывает `OK`.

### 4. Проверить master и forward zone

```bash
docker compose exec dns-client dig @dns-master web.internal A +short
docker compose exec dns-client dig @dns-master web.internal AAAA +short
docker compose exec dns-client dig @dns-master internal MX +short
docker compose exec dns-client dig @dns-master internal TXT +short
docker compose exec dns-client dig @dns-master www.internal CNAME +short
```

Ожидаются `10.10.0.20`, `fd00:10:10::20`, `mail.internal.`,
`"course=dns-project"` и `web.internal.`.

### 5. Проверить reverse zone

```bash
docker compose exec dns-client dig @dns-master -x 10.10.0.20 +short
```

Ожидаемый ответ: `web.internal.`.

### 6. Проверить slave

```bash
docker compose exec dns-client dig @dns-slave web.internal A +short
docker compose exec dns-client dig @dns-slave -x 10.10.0.20 +short
```

Slave должен вернуть те же внутренние значения, что и master.

### 7. Проверить zone transfer

```bash
docker compose exec dns-slave dig @dns-master internal AXFR
docker compose exec dns-client dig @dns-master internal AXFR
```

Первый запрос разрешен, потому что его source IP равен `10.10.0.3`. Второй
запрос должен получить `REFUSED`, потому что обычному клиенту запрещено
скачивать всю зону.

### 8. Проверить ACL и рекурсию

```bash
docker compose exec dns-client dig @dns-master cloudflare.com A
docker compose exec dns-external-client dig @dns-master cloudflare.com A
```

Доверенный клиент получает рекурсивный ответ. Внешний клиент получает отказ,
потому что external view работает без рекурсии.

### 9. Проверить DNSSEC validation

```bash
docker compose exec dns-client dig +dnssec @dns-master cloudflare.com A
docker compose exec dns-client dig +dnssec @dns-master dnssec-failed.org A
```

Для корректно подписанного домена ожидается успешный ответ, обычно с флагом
`ad`. Для домена с некорректной DNSSEC-подписью ожидается `SERVFAIL`. Эта
проверка зависит от доступа контейнера к upstream DNS.

### 10. Показать Split-Horizon DNS

```bash
docker compose exec dns-client dig @dns-master web.internal A +short
docker compose exec dns-external-client dig @dns-master web.internal A +short
```

Внутренний клиент получает `10.10.0.20`, внешний - `203.0.113.20`.

### 11. Показать logging

```bash
docker compose logs dns-master
```

После предыдущих запросов в выводе видны сообщения категории `queries`.

### 12. Показать rndc

```bash
docker compose exec dns-master rndc -c /etc/bind/rndc.conf status
docker compose exec dns-master rndc -c /etc/bind/rndc.conf reload
```

`rndc` показывает состояние BIND9 и перезагружает конфигурацию без пересоздания
контейнера.

### 13. Запустить автоматические тесты

```bash
make test
```

Ожидается успешное завершение `pytest` и сообщение `AXFR checks passed.`.

### 14. Кратко объяснить BIND9 и Unbound

BIND9 выбран как единая технология для авторитативных зон, master/slave,
рекурсии, views, `rndc` и RRL. Unbound мог бы использоваться отдельно как
рекурсивный DNS-резолвер с DNSSEC validation, но в текущем проекте он не нужен.

## Что доказывает демонстрация

- master и slave отвечают авторитативно;
- forward и reverse зоны содержат ожидаемые записи;
- zone transfer разрешен только slave-серверу;
- рекурсия ограничена доверенной сетью;
- DNSSEC validation включена;
- Split-Horizon возвращает разные ответы;
- logging, `rndc` и RRL присутствуют в конфигурации;
- тесты запускаются одной командой.
