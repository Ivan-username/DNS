# Task 03 Doc. Slave DNS, security, DNSSEC, Split-Horizon и RRL

## Краткое введение

Slave DNS, или secondary DNS, получает копии зон с master и отвечает
авторитативно теми же данными. Это повышает доступность DNS и показывает
стандартный механизм передачи зон.

Безопасность DNS в проекте состоит из нескольких частей: AXFR доступен только
slave-серверу, рекурсия ограничена ACL, DNSSEC validation проверяет внешние
ответы, Split-Horizon разделяет внутренние и внешние данные, а RRL ограничивает
частоту похожих ответов.

## Почему выбран такой способ

Slave также реализован на BIND9, потому что BIND9 напрямую поддерживает
master/slave, `notify`, AXFR и IXFR. Для Split-Horizon используется механизм
`view`, поскольку он является стандартным способом BIND9 выбирать зону по
адресу клиента.

В проекте реализована DNSSEC validation, а не подписание локальной зоны. Это
закрывает задачу проверки подлинности рекурсивных внешних ответов без
усложнения лаборатории управлением KSK/ZSK-ключами.

## Slave DNS и transfer зон

`dns-slave` имеет адрес `10.10.0.3` в сети `dns-lab`. Он получает две зоны с
master `10.10.0.2`:

- `internal`;
- `0.10.10.in-addr.arpa`.

Полученные файлы хранятся в `slave/slave-zones/`. На master для обеих зон
настроены:

```text
allow-transfer { 10.10.0.3; };
notify yes;
also-notify { 10.10.0.3; };
```

Обычному клиенту AXFR запрещен. Проверка:

```bash
docker compose exec dns-slave dig @dns-master internal AXFR
docker compose exec dns-client dig @dns-master internal AXFR
docker compose exec dns-client dig @dns-slave web.internal A +short
```

Первый запрос возвращает зону, второй получает `REFUSED`, slave отвечает
`10.10.0.20`.

## ACL и ограничение рекурсии

Открытый рекурсивный DNS-сервер опасен: его могут использовать посторонние
клиенты и DNS amplification-атаки. В master определен ACL `trusted_clients`:

```text
acl trusted_clients {
    127.0.0.1;
    10.10.0.0/24;
};
```

Во внутреннем view рекурсия и доступ к кэшу разрешены только этому ACL. Во
внешнем view рекурсия полностью отключена.

```bash
docker compose exec dns-client dig @dns-master cloudflare.com A
docker compose exec dns-external-client dig @dns-master cloudflare.com A
```

Доверенный клиент получает ответ, внешний клиент получает `REFUSED`.

## DNSSEC validation

DNSSEC добавляет цифровые подписи к DNS-данным. Validation означает проверку
чужих подписанных ответов, а signing означает подписание собственной зоны.

В `master/named.conf.options` включено:

```text
dnssec-validation auto;
```

Проверка:

```bash
docker compose exec dns-client dig +dnssec @dns-master cloudflare.com A
docker compose exec dns-client dig +dnssec @dns-master dnssec-failed.org A
```

Для `cloudflare.com` ожидается успешный ответ с DNSSEC-данными и обычно флагом
`ad`. Для намеренно сломанной DNSSEC-зоны `dnssec-failed.org` ожидается
`SERVFAIL`. Проверка зависит от доступа контейнера к upstream DNS.

Локальная зона `internal` не подписана. Это принятое ограничение проекта:
реализована DNSSEC validation для рекурсивных запросов, но не DNSSEC signing
локальной зоны.

## Split-Horizon DNS

Split-Horizon возвращает разные ответы на одно имя в зависимости от клиента.
Master подключен к двум сетям и содержит два BIND view:

| View | Клиенты | `web.internal A` | Рекурсия |
| --- | --- | --- | --- |
| `internal-view` | `10.10.0.0/24` | `10.10.0.20` | Разрешена по ACL |
| `external-view` | Остальные | `203.0.113.20` | Запрещена |

Внешний адрес взят из документационной сети `203.0.113.0/24` и используется
только для демонстрации.

```bash
docker compose exec dns-client dig @dns-master web.internal A +short
docker compose exec dns-external-client dig @dns-master web.internal A +short
```

## RRL

RRL, Response Rate Limiting, снижает риск DNS amplification, ограничивая
частоту похожих ответов. На master и slave настроен учебный лимит:

```text
rate-limit {
    responses-per-second 5;
    window 5;
};
```

Поддержка директивы подтверждается успешным `named-checkconf`. При серии
однотипных запросов события RRL видны в логах master.

```bash
docker compose exec dns-master named-checkconf /etc/bind/named.conf
docker compose logs dns-master
```

## Итоговая проверка

```bash
make check-config
make test
```

Эти команды проверяют конфигурацию, зоны, записи master/slave, latency и
ограничение AXFR.
