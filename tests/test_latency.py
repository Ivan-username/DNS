import os
import statistics
import time

import dns.message
import dns.query
import dns.rcode
import pytest

from dns_helpers import DNS_SERVERS


SAMPLE_COUNT = int(os.getenv("DNS_LATENCY_SAMPLES", "5"))
MAX_AVERAGE_MS = float(os.getenv("DNS_LATENCY_MAX_MS", "100"))


@pytest.mark.parametrize("server_name,server", DNS_SERVERS.items())
def test_average_dns_latency(server_name, server):
    request = dns.message.make_query("web.internal", "A")
    durations_ms = []

    for _ in range(SAMPLE_COUNT):
        started = time.perf_counter()
        response = dns.query.udp(request, server, timeout=2)
        durations_ms.append((time.perf_counter() - started) * 1000)

        assert response.rcode() == dns.rcode.NOERROR, (
            f"{server_name} ({server}) returned {dns.rcode.to_text(response.rcode())}"
        )
        assert response.answer, f"{server_name} ({server}) returned an empty answer"

    average_ms = statistics.mean(durations_ms)
    assert average_ms < MAX_AVERAGE_MS, (
        f"{server_name} ({server}) average latency was {average_ms:.2f} ms; "
        f"expected less than {MAX_AVERAGE_MS:.2f} ms. Samples: {durations_ms}"
    )
