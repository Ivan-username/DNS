# Ручные проверки DNS-лаборатории

## Краткое введение

Эти команды дополняют автоматические тесты и удобны для быстрой диагностики или
демонстрации отдельных функций BIND9.

## Запуск

```bash
docker compose up -d --build
docker compose ps
```

## Записи и slave

```bash
docker compose exec dns-client dig @dns-master web.internal A +short
docker compose exec dns-client dig @dns-master web.internal AAAA +short
docker compose exec dns-client dig @dns-master internal MX +short
docker compose exec dns-client dig @dns-master internal TXT +short
docker compose exec dns-client dig @dns-master www.internal CNAME +short
docker compose exec dns-client dig @dns-master -x 10.10.0.20 +short
docker compose exec dns-client dig @dns-slave web.internal A +short
```

## AXFR, ACL и Split-Horizon

```bash
docker compose exec dns-slave dig @dns-master internal AXFR
docker compose exec dns-client dig @dns-master internal AXFR
docker compose exec dns-client dig @dns-master cloudflare.com A
docker compose exec dns-external-client dig @dns-master cloudflare.com A
docker compose exec dns-client dig @dns-master web.internal A +short
docker compose exec dns-external-client dig @dns-master web.internal A +short
```

## DNSSEC, logging и rndc

```bash
docker compose exec dns-client dig +dnssec @dns-master cloudflare.com A
docker compose logs dns-master
docker compose exec dns-master rndc -c /etc/bind/rndc.conf status
docker compose exec dns-master rndc -c /etc/bind/rndc.conf reload
```

## Полная автоматическая проверка

```bash
make test
```
