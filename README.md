# DNS Course Project

Учебный проект по развертыванию локальной DNS-инфраструктуры на BIND9 в Docker Compose.

## Краткое введение

DNS переводит понятные имена, например `web.internal`, в IP-адреса, например
`10.10.0.20`. В этом проекте BIND9 одновременно показывает две роли DNS:
авторитативный сервер хранит локальные зоны, а рекурсивный резолвер ищет внешние
имена только для доверенных клиентов.

Инфраструктура включает master и slave DNS, прямую и обратную зоны, ограниченную
рекурсию, DNSSEC validation, logging, `rndc`, Split-Horizon DNS, RRL и
автоматические тесты.

## Почему выбран этот способ

BIND9 выбран потому, что одним продуктом закрывает требования учебного задания:
зоны, master/slave, AXFR, ACL, DNSSEC validation, `logging {}`, `view`, `rndc` и
RRL. Docker Compose делает лабораторию воспроизводимой, а Python, `pytest` и
`dnspython` проверяют DNS-ответы как структурированные данные.

Unbound не используется в рабочей конфигурации. Он хорошо подходит для роли
рекурсивного резолвера, но для этой лаборатории BIND9 проще и нагляднее как
единая технология.

## Итоговое решение

`dns-master` хранит исходные файлы зон `internal` и
`0.10.10.in-addr.arpa`. `dns-slave` получает их с master через AXFR/IXFR и
отвечает авторитативно. `dns-client` находится в доверенной сети и используется
для `dig`, рекурсии и Python-тестов. `dns-external-client` находится в отдельной
сети, не имеет доступа к рекурсии и получает внешний Split-Horizon ответ.

## Стек

- BIND9 на Alpine Linux;
- Docker Compose;
- `dig`, `host`, `rndc`;
- Python, `pytest`, `dnspython`;
- Bash для проверки AXFR.

## Сервисы и адреса

| Сервис | Роль | Сеть и IP |
| --- | --- | --- |
| `dns-master` | Master DNS, рекурсия, internal/external views | `10.10.0.2`, `10.20.0.2` |
| `dns-slave` | Slave DNS для внутренних зон | `10.10.0.3` |
| `dns-client` | Доверенный клиент и тесты | `10.10.0.10` |
| `dns-external-client` | Недоверенный клиент для Split-Horizon | `10.20.0.10` |

Основной домен: `internal`. Reverse zone: `0.10.10.in-addr.arpa`.

## Структура репозитория

```text
.
├── docker-compose.yml
├── Makefile
├── master/
│   ├── named.conf
│   ├── named.conf.options
│   ├── named.conf.local
│   ├── named.conf.views
│   ├── rndc.conf
│   └── zones/
├── slave/
│   ├── named.conf
│   ├── named.conf.options
│   ├── named.conf.local
│   └── slave-zones/
├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── test_records.py
│   ├── test_latency.py
│   ├── test_zone_transfer.sh
│   └── manual-checks.md
└── docs/
```

## Быстрый старт

Требуются Docker с Compose plugin и свободный порт `53/tcp` и `53/udp` на
хосте.

```bash
docker compose up -d --build
docker compose ps
```

Остановить лабораторию:

```bash
docker compose down
```

## Единый запуск тестов

Основной способ проверки проекта:

```bash
make test
```

Команда собирает и запускает контейнеры, выполняет `pytest` для записей и
latency, затем проверяет разрешенный и запрещенный AXFR.

Отдельные проверки:

```bash
make pytest
make axfr
make check-config
```

## Ручная проверка

Конфигурация и зоны:

```bash
docker compose exec dns-master named-checkconf /etc/bind/named.conf
docker compose exec dns-slave named-checkconf /etc/bind/named.conf
docker compose exec dns-master named-checkzone internal /etc/bind/zones/db.internal
docker compose exec dns-master named-checkzone internal /etc/bind/zones/db.internal.external
docker compose exec dns-master named-checkzone 0.10.10.in-addr.arpa /etc/bind/zones/db.10.10.0
```

Записи master и slave:

```bash
docker compose exec dns-client dig @dns-master web.internal A +short
docker compose exec dns-client dig @dns-master web.internal AAAA +short
docker compose exec dns-client dig @dns-master internal MX +short
docker compose exec dns-client dig @dns-master internal TXT +short
docker compose exec dns-client dig @dns-master www.internal CNAME +short
docker compose exec dns-client dig @dns-master -x 10.10.0.20 +short
docker compose exec dns-client dig @dns-slave web.internal A +short
```

Рекурсия, DNSSEC validation и ACL:

```bash
docker compose exec dns-client dig @dns-master cloudflare.com A
docker compose exec dns-client dig +dnssec @dns-master cloudflare.com A
docker compose exec dns-external-client dig @dns-master cloudflare.com A
```

Split-Horizon:

```bash
docker compose exec dns-client dig @dns-master web.internal A +short
docker compose exec dns-external-client dig @dns-master web.internal A +short
```

Ожидаются разные ответы: `10.10.0.20` и `203.0.113.20`.

Logging и `rndc`:

```bash
docker compose logs dns-master
docker compose exec dns-master rndc -c /etc/bind/rndc.conf status
docker compose exec dns-master rndc -c /etc/bind/rndc.conf reload
```

## Документация

- [Контекст, основы DNS и архитектура](docs/task-01-doc-context-architecture.md)
- [Master DNS, зоны, logging и rndc](docs/task-02-doc-infrastructure-master.md)
- [Slave DNS, security, DNSSEC, Split-Horizon и RRL](docs/task-03-doc-slave-security.md)
- [Тесты и демо-сценарий](docs/task-04-doc-tests-docs-demo.md)
- [Краткие ручные проверки](tests/manual-checks.md)

## Известные ограничения

- Локальная зона `internal` не подписана; реализована DNSSEC validation для
  рекурсивных внешних запросов.
- Рекурсивные проверки зависят от доступа Docker-контейнера к forwarders
  `1.1.1.1` и `8.8.8.8`.
- RRL включен с учебным лимитом `5` похожих ответов в секунду; это не
  производственный профиль нагрузки.
- Внешние адреса `203.0.113.0/24` используются только для демонстрации и не
  маршрутизируются в интернет.
