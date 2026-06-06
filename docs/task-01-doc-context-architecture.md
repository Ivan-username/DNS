# Task 01 Doc. Контекст проекта и базовая архитектура

## Краткое введение

Проект посвящен развертыванию локальной DNS-инфраструктуры для учебной лаборатории. DNS, Domain Name System, нужен для перевода понятных человеку имен в IP-адреса. Например, имя `web.internal` может указывать на адрес `10.10.0.20`, а reverse DNS позволяет выполнить обратную операцию: по адресу `10.10.0.20` получить имя `web.internal`.

В рамках проекта нужно показать не один отдельный DNS-запрос, а полноценную инфраструктуру: master DNS, slave DNS, локальный домен, прямую и обратную зоны, ограниченную рекурсию, DNSSEC validation, logging, transfer зон, Split-Horizon DNS, `rndc`, RRL, тесты и документацию.

## Почему выбран такой способ

Основная технология проекта - BIND9. Он выбран потому, что закрывает почти все требования задания одним продуктом:

- авторитативные зоны;
- прямые и обратные DNS-зоны;
- рекурсивные запросы;
- ACL для ограничения клиентов;
- DNSSEC validation;
- master/slave и AXFR/IXFR;
- Split-Horizon через `view`;
- logging через `logging {}`;
- управление через `rndc`;
- RRL, если сборка BIND поддерживает `rate-limit`.

Unbound в рабочей конфигурации пока не используется. Его роль нужно объяснить отдельно как альтернативный рекурсивный резолвер. Для учебного проекта проще и нагляднее реализовать все обязательные возможности на BIND9, чем разделять авторитативную и рекурсивную роли между разными DNS-серверами.

Docker Compose выбран как будущий способ запуска DNS-инфраструктуры, потому что он делает лабораторию воспроизводимой. Один набор файлов должен поднимать одинаковую инфраструктуру на любой машине с Docker: master, slave и тестовые клиенты.

## BIND9 и Unbound в рамках задания

В задании разрешены BIND9 или Unbound, но эти инструменты удобны для разных ролей.

BIND9 подходит для этого проекта как основной DNS-сервер, потому что умеет одновременно быть авторитативным сервером для локальной зоны `internal` и рекурсивным резолвером для доверенных клиентов. К требованиям задания на стороне BIND9 относятся forward/reverse зоны, master/slave, AXFR/IXFR, ACL, DNSSEC validation, `logging {}`, `rndc`, Split-Horizon через `view` и RRL.

Unbound чаще используют как быстрый и безопасный рекурсивный резолвер. Он хорошо подходит для кэширующей рекурсии и DNSSEC validation, но не является удобной заменой BIND9 для полной авторитативной master/slave-инфраструктуры с zone transfer и `rndc`.

Использовать BIND9 и Unbound вместе технически можно: например, BIND9 отвечает за авторитативные зоны, а Unbound обслуживает рекурсивные запросы клиентов. В этом учебном проекте такой вариант пока не реализуется, потому что он усложняет Docker Compose, тесты и защиту проекта без необходимости для базовой сдачи. Поэтому рабочая конфигурация строится на BIND9, а Unbound описывается в документации как альтернатива для рекурсивной роли.

## Текущая архитектура репозитория

Сейчас проект находится на подготовительном этапе. В корне репозитория есть инструкции агента, публичная документация и пустой каталог `src/`. Рабочие task-файлы, исходное задание и черновики перенесены в `.ai/`, чтобы изолировать процессуальные материалы от git.

Текущая структура:

```text
dns-course-project/
├── AGENTS.md
├── docs/
│   ├── task-01-doc-context-architecture.md
│   ├── task-02-doc-infrastructure-master.md
│   ├── task-03-doc-slave-security.md
│   └── task-04-doc-tests-docs-demo.md
├── src/
└── .ai/
    ├── origin/
    │   ├── purpose.md
    │   └── projects.pdf
    ├── tasks/
    │   ├── task-01.md
    │   ├── task-02-infrastructure-master.md
    │   ├── task-03-slave-security.md
    │   └── task-04-tests-docs-demo.md
    ├── drafts/
    ├── prompts/
    ├── context/
    └── runs/
```

На текущем этапе в проекте еще нет `docker-compose.yml`, `master/`, `slave/`, `tests/` и `README.md`. Эти элементы относятся к целевой DNS-архитектуре и должны появиться при выполнении следующих задач.

## Целевая архитектура

Базовая схема DNS-инфраструктуры после реализации:

```text
docker network: dns-lab, 10.10.0.0/24

dns-client
    |
    | dig / host / pytest
    v
dns-master ------------------> dns-slave
10.10.0.2       AXFR/IXFR      10.10.0.3
    |
    | recursion only for trusted clients
    v
external DNS / upstream resolvers
```

Основные роли:

- `dns-master` хранит исходные файлы зон и является главным авторитативным сервером для домена `internal`;
- `dns-slave` получает копии зон с master и тоже отвечает авторитативно;
- `dns-client` используется для ручных проверок через `dig`/`host` и автоматических тестов через `pytest`;
- internal/external clients могут использоваться для демонстрации Split-Horizon DNS.

## Базовые значения проекта

| Параметр | Значение |
| --- | --- |
| Основной домен | `internal` |
| Docker-сеть | `10.10.0.0/24` |
| Master DNS | `10.10.0.2` |
| Slave DNS | `10.10.0.3` |
| Reverse zone | `0.10.10.in-addr.arpa` |
| Пример web-сервиса | `10.10.0.20` |
| Пример api-сервиса | `10.10.0.21` |
| Пример mail-сервиса | `10.10.0.30` |

Эти значения считаются принятыми решениями. Их не нужно менять без явной причины, потому что от них зависят конфигурация зон, Docker Compose, тесты и документация.

## Термины

- Авторитативный DNS-сервер хранит зону и дает окончательный ответ по именам этой зоны.
- Рекурсивный DNS-сервер ищет ответ для клиента у других DNS-серверов.
- Forward zone переводит имя в IP-адрес, например `web.internal` -> `10.10.0.20`.
- Reverse zone переводит IP-адрес в имя через PTR-запись.
- Master DNS хранит исходную копию зоны.
- Slave DNS получает копию зоны с master через zone transfer.
- AXFR - полный transfer зоны.
- ACL ограничивает доступ по IP-адресам или подсетям.
- DNSSEC validation проверяет подлинность внешних DNS-ответов.
- Split-Horizon DNS возвращает разные ответы разным группам клиентов.
- RRL ограничивает частоту однотипных DNS-ответов.
- `rndc` управляет BIND9 без полного перезапуска сервера.

## Разделение задач

Проект делится на четыре логические задачи:

- Task 01 фиксирует контекст, архитектуру и принятые решения.
- Task 02 поднимает Docker Compose, master DNS, зоны, logging и `rndc`.
- Task 03 добавляет slave DNS, AXFR, ACL, DNSSEC validation, Split-Horizon и RRL.
- Task 04 добавляет автоматические тесты, README, дополнительные документы и демо-сценарий.

Такое разделение удобно для работы двух человек. Один участник может взять инфраструктуру и master DNS, второй - безопасность, slave, тесты и документацию.

Рекомендуемое разделение:

- Участник 1 выполняет Task 02: создает Docker Compose, образ master-сервера, конфигурацию BIND9 master, forward/reverse зоны, базовые записи, logging, `rndc` и первичные команды ручной проверки.
- Участник 2 выполняет Task 03 и Task 04: добавляет slave DNS, ограниченный zone transfer, ACL для рекурсии, DNSSEC validation, Split-Horizon, RRL, автоматические тесты, README и демо-сценарий.

Task 01 не создает рабочую DNS-инфраструктуру. В рамках этой задачи не нужно добавлять `docker-compose.yml`, каталоги `master/`, `slave/`, `tests/` или `README.md`; они появляются только при выполнении следующих task-файлов.

## Целевая структура после реализации DNS

```text
dns-course-project/
├── docker-compose.yml
├── README.md
├── AGENTS.md
├── .ai/
│   ├── origin/
│   ├── tasks/
│   ├── drafts/
│   ├── prompts/
│   ├── context/
│   └── runs/
├── master/
│   ├── Dockerfile
│   ├── named.conf
│   ├── named.conf.options
│   ├── named.conf.local
│   ├── named.conf.views
│   ├── rndc.conf
│   ├── zones/
│   ├── keys/
│   └── logs/
├── slave/
│   ├── Dockerfile
│   ├── named.conf
│   ├── named.conf.options
│   ├── named.conf.local
│   ├── slave-zones/
│   └── logs/
├── tests/
│   ├── requirements.txt
│   ├── test_records.py
│   ├── test_latency.py
│   ├── test_zone_transfer.sh
│   └── manual-checks.md
└── docs/
    ├── task-01-doc-context-architecture.md
    ├── task-02-doc-infrastructure-master.md
    ├── task-03-doc-slave-security.md
    └── task-04-doc-tests-docs-demo.md
```

Процессуальные файлы агента и черновики остаются в `.ai/`, чтобы не смешивать рабочий проект и внутренние материалы планирования.

## Общие команды проверки

После реализации инфраструктуры основной сценарий проверки должен выглядеть так:

```bash
docker compose up -d --build
docker compose ps

docker compose exec dns-client dig @dns-master web.internal A
docker compose exec dns-client dig @dns-master web.internal AAAA
docker compose exec dns-client dig @dns-master internal MX
docker compose exec dns-client dig @dns-master internal TXT
docker compose exec dns-client dig @dns-master -x 10.10.0.20

docker compose exec dns-client dig @dns-slave web.internal A
docker compose exec dns-client pytest tests
```

Конкретные команды для каждой части проекта описаны в документации соответствующих задач.

## Критерии готовности Task 01

- Зафиксированы принятые решения по BIND9, домену, IP-адресам и Docker-сети.
- Понятно, какие компоненты нужно реализовать в следующих задачах.
- Есть разделение работ между участниками.
- Документация объясняет DNS с базового уровня и связывает термины с требованиями задания.
- Проект можно продолжать без дополнительного устного контекста.
