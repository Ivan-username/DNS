# DNS Course Project

Учебный проект по развертыванию локальной DNS-инфраструктуры на BIND9 в Docker Compose.

## Краткое введение

DNS переводит имена вроде `web.internal` в IP-адреса вроде `10.10.0.20`. Master DNS, или primary DNS, хранит исходные файлы зон и является главным источником правды для домена.

Forward zone отвечает за прямые запросы: имя -> IP-адрес. Reverse zone отвечает за обратные запросы: IP-адрес -> имя через PTR-записи. В этом проекте master обслуживает домен `internal` и reverse zone `0.10.10.in-addr.arpa`.

Logging через BIND `logging {}` нужен, чтобы видеть DNS-запросы и события сервера. `rndc` нужен для управления BIND9 без пересоздания контейнера: например, для проверки статуса и перезагрузки зон.

## Почему BIND9 в Docker Compose

BIND9 выбран потому, что он закрывает требования задания: авторитативные зоны, reverse DNS, рекурсию, ACL, DNSSEC validation, logging, `rndc`, а на следующих этапах zone transfer, Split-Horizon и RRL.

Docker Compose делает лабораторный стенд воспроизводимым: `dns-master` запускает BIND9, а `dns-client` содержит `dig` и `host` для ручных проверок.

## Реализовано на этом этапе

- `dns-master` на BIND9 в Alpine Linux.
- `dns-client` для проверок.
- Docker-сеть `dns-lab`: `10.10.0.0/24`.
- Master DNS: `10.10.0.2`.
- Forward zone: `internal`.
- Reverse zone: `0.10.10.in-addr.arpa`.
- Записи A, AAAA, MX, TXT, CNAME и PTR.
- DNSSEC validation для рекурсивных запросов.
- Рекурсивные запросы от доверенной сети через upstream forwarders `1.1.1.1` и `8.8.8.8`.
- Logging через BIND `logging {}` в `docker compose logs dns-master`.
- `rndc status` и `rndc reload`.

## Структура

```text
docker-compose.yml
master/
├── Dockerfile
├── named.conf
├── named.conf.options
├── named.conf.local
├── rndc.conf
├── rndc.key
├── keys/
├── logs/
└── zones/
    ├── db.internal
    └── db.10.10.0
slave/
tests/
```

## Запуск

```bash
docker compose up -d --build
```

Проверить, что контейнеры запущены:

```bash
docker compose ps
```

## Проверка конфигурации BIND

```bash
docker compose exec dns-master named-checkconf /etc/bind/named.conf
```

Проверить forward zone:

```bash
docker compose exec dns-master named-checkzone internal /etc/bind/zones/db.internal
```

Проверить reverse zone:

```bash
docker compose exec dns-master named-checkzone 0.10.10.in-addr.arpa /etc/bind/zones/db.10.10.0
```

## Проверка DNS-записей

Forward zone:

```bash
docker compose exec dns-client dig @10.10.0.2 web.internal A +short
docker compose exec dns-client dig @10.10.0.2 web.internal AAAA +short
docker compose exec dns-client dig @10.10.0.2 internal MX +short
docker compose exec dns-client dig @10.10.0.2 internal TXT +short
docker compose exec dns-client dig @10.10.0.2 www.internal CNAME +short
```

Reverse zone:

```bash
docker compose exec dns-client dig @10.10.0.2 -x 10.10.0.20 +short
```

## Проверка логов

```bash
docker compose logs dns-master
```

После DNS-запросов в логах должны появляться события категории `queries`.

## Проверка rndc

```bash
docker compose exec dns-master rndc -c /etc/bind/rndc.conf status
docker compose exec dns-master rndc -c /etc/bind/rndc.conf reload
```

## Остановка

```bash
docker compose down
```
