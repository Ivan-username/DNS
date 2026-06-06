import os
import time

import dns.exception
import dns.resolver


MASTER_DNS = os.getenv("MASTER_DNS", "10.10.0.2")
SLAVE_DNS = os.getenv("SLAVE_DNS", "10.10.0.3")
DNS_SERVERS = {
    "master": MASTER_DNS,
    "slave": SLAVE_DNS,
}


def query(server: str, name: str, record_type: str, attempts: int = 5):
    """Resolve one record with short retries while containers finish starting."""
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [server]
    resolver.timeout = 1
    resolver.lifetime = 2

    last_error = None
    for attempt in range(attempts):
        try:
            return resolver.resolve(name, record_type, search=False)
        except dns.exception.DNSException as error:
            last_error = error
            if attempt < attempts - 1:
                time.sleep(0.5)

    raise AssertionError(
        f"{server} did not answer {name} {record_type}: {last_error}"
    ) from last_error
