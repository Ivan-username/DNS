# Task 02 Doc. Docker Compose, Master DNS, зоны, logging и rndc

## Краткое введение

Task 02 создает базовую инфраструктуру проекта: Docker Compose, master DNS на BIND9, forward zone, reverse zone, logging и `rndc`. После этой задачи проект должен уметь запускать master-сервер и отвечать на основные DNS-запросы по локальному домену `internal`.

Master DNS, или primary DNS, хранит исходные файлы зон. В этой лаборатории он отвечает за домен `internal`, прямые записи вроде `web.internal A 10.10.0.20` и обратные PTR-записи для адресов из сети `10.10.0.0/24`.

## Почему выбран такой способ

BIND9 выбран для master DNS, потому что он является полноценным авторитативным DNS-сервером и поддерживает все нужные механизмы: зоны, reverse DNS, logging, `rndc`, ACL, DNSSEC и transfer зон. В Task 02 реализуется фундамент, на который затем опираются security и slave-настройки из Task 03.

Docker Compose используется для воспроизводимости. Проверяющий должен иметь возможность выполнить одну команду и получить одинаковую лабораторную среду: master DNS и клиентский контейнер для `dig`, `host` и будущих Python-тестов.

Файлы зон хранятся явно в репозитории. Это проще для учебного проекта: записи можно открыть, прочитать, проверить через `named-checkzone` и объяснить на защите.

## Что реализует задача

Текущее состояние перед Task 02: DNS-сервисы еще не созданы. В репозитории уже есть `AGENTS.md`, документы в `docs/`, пустой `src/` и процессуальные материалы в `.ai/`. Task 02 должна стать первым практическим шагом, который добавит рабочую Docker/BIND-часть в корень проекта.

В результате Task 02 должны появиться:

- `docker-compose.yml` с сервисами `dns-master` и `dns-client`;
- `master/Dockerfile` на Alpine Linux с BIND9 и утилитами проверки;
- главный конфиг BIND9 `master/named.conf`;
- настройки сервера в `master/named.conf.options`;
- подключение зон в `master/named.conf.local`;
- forward zone `master/zones/db.internal`;
- reverse zone `master/zones/db.10.10.0`;
- logging через BIND `logging {}`;
- `rndc` для управления сервером без полного перезапуска;
- команды запуска и проверки в README или документации.

После Task 02 текущая архитектура репозитория должна измениться так: в корне появятся `docker-compose.yml`, `README.md`, каталог `master/` с конфигурацией BIND9 и каталог `tests/` или клиентская часть, если она нужна для проверок. `slave/` может быть создан как пустая заготовка, но полноценный slave DNS реализуется в Task 03.

## Docker Compose

Целевая схема после выполнения Task 02:

```text
dns-lab network: 10.10.0.0/24

dns-client  ->  dns-master
               10.10.0.2
```

Требования к `dns-master`:

- статический IP `10.10.0.2`;
- BIND9 запускается в foreground;
- порт `53/udp` и `53/tcp` доступен для DNS-запросов;
- конфигурация и зоны подключены как volume или копируются в образ;
- каталог логов доступен для просмотра.

Требования к `dns-client`:

- находится в той же Docker-сети;
- имеет утилиты `dig` и `host`;
- позднее может запускать Python-тесты.

Перед запуском полезно проверить Compose-файл:

```bash
docker compose config
```

## Конфигурация BIND9 master

Рекомендуемое разделение конфигов:

- `named.conf` - главный файл, который подключает остальные части;
- `named.conf.options` - общие настройки BIND9;
- `named.conf.local` - локальные зоны;
- `rndc.conf` и ключ `rndc` - управление сервером;
- `zones/db.internal` - forward zone;
- `zones/db.10.10.0` - reverse zone.

Минимальные настройки `options`:

```text
options {
    directory "/var/cache/bind";
    listen-on port 53 { any; };
    listen-on-v6 { none; };
    dnssec-validation auto;
};
```

ACL для рекурсии можно подготовить уже здесь или оставить для Task 03. Если настройка временная, это должно быть явно отмечено комментарием в конфиге и документации.

## Forward zone `internal`

Forward zone переводит имена в IP-адреса. Для проекта нужна зона `internal`.

Минимальные записи:

```text
internal.       SOA ns1.internal. admin.internal.
internal.       NS  ns1.internal.
internal.       NS  ns2.internal.
ns1             A   10.10.0.2
ns2             A   10.10.0.3
web             A   10.10.0.20
api             A   10.10.0.21
mail            A   10.10.0.30
web             AAAA fd00:10:10::20
internal.       MX  10 mail.internal.
internal.       TXT "course=dns-project"
www             CNAME web.internal.
```

В зоне должен быть корректный SOA serial. При каждом изменении зоны serial нужно увеличивать, иначе slave DNS из Task 03 может не забрать обновления.

Проверка зоны:

```bash
docker compose exec dns-master named-checkzone internal /etc/bind/zones/db.internal
```

## Reverse zone `0.10.10.in-addr.arpa`

Reverse zone переводит IP-адреса обратно в имена. Для сети `10.10.0.0/24` используется зона `0.10.10.in-addr.arpa`.

Минимальные PTR-записи:

```text
2   PTR ns1.internal.
3   PTR ns2.internal.
20  PTR web.internal.
21  PTR api.internal.
30  PTR mail.internal.
```

Проверка зоны:

```bash
docker compose exec dns-master named-checkzone 0.10.10.in-addr.arpa /etc/bind/zones/db.10.10.0
```

Ручная проверка reverse lookup:

```bash
docker compose exec dns-client dig @dns-master -x 10.10.0.20
```

## Logging

Logging нужен, чтобы показать, что BIND9 реально получает и обрабатывает запросы. Это отдельный пункт задания, поэтому нужно использовать именно BIND `logging {}`.

Минимально стоит настроить каналы:

- `queries` для DNS-запросов;
- `security` для событий безопасности;
- `default` для общих сообщений.

Проверка логов:

```bash
docker compose logs dns-master
```

или, если логи пишутся в файл:

```bash
docker compose exec dns-master tail -f /var/log/bind/queries.log
```

## rndc

`rndc` позволяет управлять BIND9 без полного перезапуска контейнера. Для защиты используется ключ, который должен быть известен `named` и клиенту `rndc`.

Минимальные проверки:

```bash
docker compose exec dns-master rndc status
docker compose exec dns-master rndc reload
```

Если ключ генерируется внутри контейнера, команду генерации нужно описать в README или документации. Важно не путать `rndc reload` и перезапуск контейнера: `rndc reload` перечитывает конфигурацию или зоны средствами самого BIND9.

## Ручные команды проверки

Запуск:

```bash
docker compose up -d --build
docker compose ps
```

Проверка конфигурации:

```bash
docker compose exec dns-master named-checkconf
docker compose exec dns-master named-checkzone internal /etc/bind/zones/db.internal
docker compose exec dns-master named-checkzone 0.10.10.in-addr.arpa /etc/bind/zones/db.10.10.0
```

Проверка записей:

```bash
docker compose exec dns-client dig @dns-master web.internal A
docker compose exec dns-client dig @dns-master web.internal AAAA
docker compose exec dns-client dig @dns-master internal MX
docker compose exec dns-client dig @dns-master internal TXT
docker compose exec dns-client dig @dns-master www.internal CNAME
docker compose exec dns-client dig @dns-master -x 10.10.0.20
```

Проверка logging и `rndc`:

```bash
docker compose logs dns-master
docker compose exec dns-master rndc status
docker compose exec dns-master rndc reload
```

## Критерии готовности Task 02

- `docker compose up -d --build` поднимает `dns-master` и `dns-client`.
- `docker compose config` проходит без ошибок.
- `named-checkconf` проходит без ошибок.
- Forward zone `internal` проходит `named-checkzone`.
- Reverse zone `0.10.10.in-addr.arpa` проходит `named-checkzone`.
- Master отвечает на A, AAAA, MX, TXT, CNAME и PTR.
- Logging показывает DNS-запросы.
- `rndc status` и `rndc reload` работают.
- В README или docs есть команды запуска и ручной проверки.
