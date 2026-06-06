.PHONY: up test pytest axfr check-config down

up:
	docker compose up -d --build

test: up
	docker compose exec -T dns-client pytest tests
	bash tests/test_zone_transfer.sh

pytest:
	docker compose exec -T dns-client pytest tests

axfr:
	bash tests/test_zone_transfer.sh

check-config:
	docker compose config
	docker compose exec -T dns-master named-checkconf /etc/bind/named.conf
	docker compose exec -T dns-slave named-checkconf /etc/bind/named.conf
	docker compose exec -T dns-master named-checkzone internal /etc/bind/zones/db.internal
	docker compose exec -T dns-master named-checkzone internal /etc/bind/zones/db.internal.external
	docker compose exec -T dns-master named-checkzone 0.10.10.in-addr.arpa /etc/bind/zones/db.10.10.0

down:
	docker compose down
