# Task 02 Doc. Docker Compose, Master DNS, зоны, logging и rndc

## Краткое введение

Master DNS, или primary DNS, хранит исходные файлы зон и является главным
источником данных для локального домена. В этой лаборатории master отвечает за
домен `internal`, прямые записи имен и обратные PTR-записи для сети
`10.10.0.0/24`.

Forward zone переводит имя в адрес, например `web.internal -> 10.10.0.20`.
Reverse zone выполняет обратную операцию:
`10.10.0.20 -> web.internal`.

## Почему выбран такой способ

BIND9 выбран как master DNS, потому что поддерживает авторитативные зоны,
logging, `rndc`, ACL, DNSSEC, transfer зон и Split-Horizon в одном продукте.
Docker Compose делает запуск воспроизводимым, а явные текстовые файлы зон легко
читать, проверять и показывать на защите.

Logging настроен через встроенный блок BIND `logging {}`, потому что это
отдельное требование задания. `rndc` используется для управления работающим
сервером без пересоздания контейнера.

## Реализованное решение

Сервис `dns-master` собирается из `master/Dockerfile`, использует Alpine Linux и
BIND9, слушает DNS на TCP/UDP порту `53` и подключен к двум сетям:

| Интерфейс | IP | Назначение |
| --- | --- | --- |
| `dns-lab` | `10.10.0.2` | Внутренние клиенты, slave и рекурсия |
| `dns-external` | `10.20.0.2` | Внешний Split-Horizon view |

Основные файлы:

| Файл | Назначение |
| --- | --- |
| `master/named.conf` | Главный конфиг, controls и logging |
| `master/named.conf.options` | ACL, forwarders, DNSSEC validation и RRL |
| `master/named.conf.views` | Internal и external views |
| `master/named.conf.local` | Внутренние master-зоны |
| `master/rndc.conf`, `master/rndc.key` | Управление через `rndc` |
| `master/zones/db.internal` | Внутренняя forward zone |
| `master/zones/db.internal.external` | Внешняя версия forward zone |
| `master/zones/db.10.10.0` | Reverse zone |

## Forward zone

Зона `internal` содержит записи:

| Имя | Тип | Значение |
| --- | --- | --- |
| `web.internal` | `A` | `10.10.0.20` |
| `web.internal` | `AAAA` | `fd00:10:10::20` |
| `api.internal` | `A` | `10.10.0.21` |
| `mail.internal` | `A` | `10.10.0.30` |
| `internal` | `MX` | `10 mail.internal` |
| `internal` | `TXT` | `course=dns-project` |
| `www.internal` | `CNAME` | `web.internal` |

Проверка:

```bash
docker compose exec dns-master named-checkzone internal /etc/bind/zones/db.internal
docker compose exec dns-client dig @dns-master web.internal A +short
docker compose exec dns-client dig @dns-master web.internal AAAA +short
docker compose exec dns-client dig @dns-master internal MX +short
docker compose exec dns-client dig @dns-master internal TXT +short
docker compose exec dns-client dig @dns-master www.internal CNAME +short
```

## Reverse zone

Зона `0.10.10.in-addr.arpa` содержит PTR-записи для `ns1`, `ns2`, `web`,
`api` и `mail`.

Проверка:

```bash
docker compose exec dns-master named-checkzone 0.10.10.in-addr.arpa /etc/bind/zones/db.10.10.0
docker compose exec dns-client dig @dns-master -x 10.10.0.20 +short
```

Ожидаемый PTR-ответ: `web.internal.`.

## Logging

В `master/named.conf` настроены каналы и категории `default`, `queries` и
`security`. Вывод направляется в stderr контейнера, поэтому запросы и события
безопасности видны через Docker logs.

```bash
docker compose exec dns-client dig @dns-master web.internal A
docker compose logs dns-master
```

## rndc

`rndc` отправляет аутентифицированные управляющие команды работающему BIND9.
Master принимает их на `127.0.0.1:953` с ключом `rndc-key`.

```bash
docker compose exec dns-master rndc -c /etc/bind/rndc.conf status
docker compose exec dns-master rndc -c /etc/bind/rndc.conf reload
```

## Проверка конфигурации

```bash
docker compose up -d --build
docker compose exec dns-master named-checkconf /etc/bind/named.conf
make check-config
```

`make check-config` также проверяет slave-конфигурацию и все файлы зон.
