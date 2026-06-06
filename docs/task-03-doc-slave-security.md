# Task 03 Doc. Slave DNS, zone transfer, ACL, DNSSEC, Split-Horizon и RRL

## Краткое введение

Task 03 добавляет отказоустойчивость и безопасность. После Task 02 есть master DNS, который хранит локальные зоны. Task 03 расширяет эту схему: добавляет slave DNS, ограничивает transfer зон, закрывает открытую рекурсию, включает DNSSEC validation, реализует Split-Horizon DNS и настраивает RRL или документирует ограничение реализации.

Slave DNS, или secondary DNS, хранит копию зоны master-сервера. Если master недоступен или нужно распределить нагрузку, slave может отвечать на DNS-запросы сам. Копирование зоны выполняется через zone transfer, обычно AXFR.

## Почему выбран такой способ

Slave тоже реализуется на BIND9, потому что BIND9 естественно поддерживает роли master и slave, директивы `allow-transfer`, `masters`, `notify`, `also-notify` и одинаковый формат зон.

DNSSEC реализуется в базовом варианте validation. Это значит, что сервер проверяет подлинность внешних DNS-ответов при рекурсивных запросах. Подписание локальной зоны `internal` не является обязательным для сдачи, потому что оно добавляет управление ключами и усложняет проект. Если время останется, signing можно добавить как расширение.

Split-Horizon реализуется через BIND `view`. Это стандартный механизм BIND9, позволяющий вернуть разные ответы для одного и того же имени разным клиентам. Для демонстрации желательно иметь internal client и external client.

RRL нужен для снижения риска DNS Amplification. Если конкретная сборка BIND9 не поддерживает директиву `rate-limit`, это нужно честно зафиксировать в документации и показать, что ограничение проверялось через `named-checkconf`.

## Slave DNS

Текущее состояние перед Task 03 зависит от выполнения Task 02. Если Task 02 еще не реализована, в репозитории нет `docker-compose.yml`, `master/` и рабочих зон, поэтому сначала нужно создать master DNS. Если Task 02 выполнена, Task 03 расширяет уже существующую архитектуру и добавляет `dns-slave`, security-настройки и Split-Horizon.

Целевая схема после выполнения Task 03:

```text
dns-master 10.10.0.2  --AXFR/IXFR-->  dns-slave 10.10.0.3
```

В Docker Compose нужно добавить сервис `dns-slave`:

- статический IP `10.10.0.3`;
- BIND9 на Alpine Linux;
- отдельная конфигурация в `slave/`;
- каталог `slave/slave-zones/` для полученных зон;
- доступность из сети `dns-lab`.

В `slave/named.conf.local` должны быть зоны:

```text
zone "internal" {
    type slave;
    masters { 10.10.0.2; };
    file "/var/cache/bind/slave-zones/db.internal";
};

zone "0.10.10.in-addr.arpa" {
    type slave;
    masters { 10.10.0.2; };
    file "/var/cache/bind/slave-zones/db.10.10.0";
};
```

После запуска slave должен получить зоны автоматически и отвечать на те же авторитативные запросы, что и master.

Проверка:

```bash
docker compose exec dns-client dig @dns-slave web.internal A
docker compose exec dns-client dig @dns-slave -x 10.10.0.20
```

## Ограничение zone transfer

AXFR не должен быть открыт для всех клиентов. Иначе любой клиент сможет выгрузить всю зону целиком и увидеть внутренние имена.

На master transfer должен быть разрешен только slave-серверу:

```text
allow-transfer { 10.10.0.3; };
notify yes;
also-notify { 10.10.0.3; };
```

Проверки:

```bash
docker compose exec dns-client dig @dns-slave web.internal A
docker compose exec dns-client dig @dns-master internal AXFR
```

Если `dns-client` не должен иметь право AXFR, команда с `dns-client` должна показать отказ. Для позитивной проверки можно выполнить AXFR из контейнера slave или проверить, что slave получил файлы зон и отвечает на записи.

## ACL и ограничение рекурсии

Открытая рекурсия опасна: чужие клиенты могут использовать сервер как публичный резолвер и участвовать в amplification-атаках. Поэтому рекурсия должна быть доступна только доверенным клиентам.

Базовый ACL:

```text
acl "trusted" {
    10.10.0.0/24;
    localhost;
    localnets;
};
```

Рекомендуемые настройки:

```text
recursion yes;
allow-recursion { trusted; };
allow-query-cache { trusted; };
```

Проверка из доверенного клиента:

```bash
docker compose exec dns-client dig @dns-master google.com A
```

Если добавлен external client из другой сети, нужно проверить, что он не может использовать рекурсию:

```bash
docker compose exec dns-external-client dig @dns-master google.com A
```

Ожидаемый результат для недоверенного клиента - отказ или отсутствие рекурсивного ответа.

## DNSSEC validation

DNSSEC защищает от подмены DNS-ответов с помощью цифровых подписей. В этом проекте обязательна DNSSEC validation для рекурсивных запросов.

Минимальная настройка:

```text
dnssec-validation auto;
```

Проверка:

```bash
docker compose exec dns-client dig +dnssec @dns-master cloudflare.com A
```

Что важно объяснить в документации:

- validation и signing - разные вещи;
- validation проверяет внешние подписанные ответы;
- signing подписывает собственную зону;
- локальная зона `internal` может оставаться неподписанной, если это явно описано как принятое ограничение.

## Split-Horizon DNS

Split-Horizon DNS возвращает разные ответы в зависимости от клиента. Например, внутренний клиент получает внутренний адрес сервиса, а внешний - публичный или демонстрационный адрес.

Пример:

| Клиент | Запрос | Ответ |
| --- | --- | --- |
| Internal client | `web.internal A` | `10.10.0.20` |
| External client | `web.internal A` | `203.0.113.20` |

Рекомендуемая реализация:

- `internal-view` для клиентов `10.10.0.0/24`;
- `external-view` для остальных клиентов;
- отдельная зона `master/zones/db.internal.external` для внешних ответов.

Важно: views не должны сломать transfer зон на slave. Если slave получает внутреннюю зону, master должен явно разрешать slave доступ к нужному view или использовать отдельные настройки, которые не блокируют AXFR.

Проверки:

```bash
docker compose exec dns-client dig @dns-master web.internal A
docker compose exec dns-external-client dig @dns-master web.internal A
```

Если отдельная внешняя сеть пока не создана, нужно документировать точную команду или compose-расширение для проверки external view.

## RRL

RRL, Response Rate Limiting, ограничивает частоту похожих DNS-ответов. Это снижает риск DNS Amplification, когда злоумышленник отправляет много запросов с подмененным source IP и заставляет DNS-сервер отвечать жертве.

Пример настройки:

```text
rate-limit {
    responses-per-second 5;
    window 5;
};
```

После добавления RRL обязательно выполнить:

```bash
docker compose exec dns-master named-checkconf
```

Если BIND9 в выбранном Alpine-образе не поддерживает `rate-limit`, это не нужно скрывать. В документации следует написать, что поддержка RRL проверена, но конкретная сборка BIND не приняла директиву; тогда ограничение реализации считается документированным.

## Ручные команды проверки

Запуск:

```bash
docker compose up -d --build
docker compose ps
```

Проверка конфигурации:

```bash
docker compose exec dns-master named-checkconf
docker compose exec dns-slave named-checkconf
```

Проверка master/slave:

```bash
docker compose exec dns-client dig @dns-master web.internal A
docker compose exec dns-client dig @dns-slave web.internal A
docker compose exec dns-client dig @dns-master -x 10.10.0.20
docker compose exec dns-client dig @dns-slave -x 10.10.0.20
```

Проверка рекурсии и DNSSEC:

```bash
docker compose exec dns-client dig @dns-master google.com A
docker compose exec dns-client dig +dnssec @dns-master cloudflare.com A
```

Проверка AXFR:

```bash
docker compose exec dns-client dig @dns-master internal AXFR
```

Проверка Split-Horizon:

```bash
docker compose exec dns-client dig @dns-master web.internal A
docker compose exec dns-external-client dig @dns-master web.internal A
```

## Критерии готовности Task 03

- `dns-slave` запускается и отвечает на запросы.
- Slave получает forward и reverse zones с master.
- AXFR разрешен только slave-серверу.
- Рекурсия доступна только trusted-клиентам.
- DNSSEC validation включена и проверяется через `dig +dnssec`.
- Split-Horizon возвращает разные ответы для internal и external клиентов или имеет документированный способ проверки.
- RRL включен или ограничение поддержки RRL документировано.
- `named-checkconf` проходит на master и slave.
- Документация объясняет ACL, AXFR, DNSSEC, Split-Horizon и RRL простым языком.
