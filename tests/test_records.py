import dns.flags
import pytest

from dns_helpers import DNS_SERVERS, query


@pytest.mark.parametrize("server_name,server", DNS_SERVERS.items())
def test_server_answers_authoritatively(server_name, server):
    answer = query(server, "web.internal", "A")

    assert answer.response.flags & dns.flags.AA, (
        f"{server_name} ({server}) answered without the authoritative AA flag"
    )
    assert {rdata.address for rdata in answer} == {"10.10.0.20"}


@pytest.mark.parametrize("server_name,server", DNS_SERVERS.items())
def test_a_record(server_name, server):
    answer = query(server, "web.internal", "A")
    actual = {rdata.address for rdata in answer}

    assert actual == {"10.10.0.20"}, (
        f"{server_name} ({server}) returned unexpected web.internal A records: {actual}"
    )


@pytest.mark.parametrize("server_name,server", DNS_SERVERS.items())
def test_aaaa_record(server_name, server):
    answer = query(server, "web.internal", "AAAA")
    actual = {rdata.address for rdata in answer}

    assert actual == {"fd00:10:10::20"}, (
        f"{server_name} ({server}) returned unexpected web.internal AAAA records: {actual}"
    )


@pytest.mark.parametrize("server_name,server", DNS_SERVERS.items())
def test_mx_record(server_name, server):
    answer = query(server, "internal", "MX")
    actual = {(rdata.preference, str(rdata.exchange).rstrip(".")) for rdata in answer}

    assert actual == {(10, "mail.internal")}, (
        f"{server_name} ({server}) returned unexpected internal MX records: {actual}"
    )


@pytest.mark.parametrize("server_name,server", DNS_SERVERS.items())
def test_txt_record(server_name, server):
    answer = query(server, "internal", "TXT")
    actual = {b"".join(rdata.strings).decode("utf-8") for rdata in answer}

    assert actual == {"course=dns-project"}, (
        f"{server_name} ({server}) returned unexpected internal TXT records: {actual}"
    )


@pytest.mark.parametrize("server_name,server", DNS_SERVERS.items())
def test_cname_record(server_name, server):
    answer = query(server, "www.internal", "CNAME")
    actual = {str(rdata.target).rstrip(".") for rdata in answer}

    assert actual == {"web.internal"}, (
        f"{server_name} ({server}) returned unexpected www.internal CNAME records: {actual}"
    )


@pytest.mark.parametrize("server_name,server", DNS_SERVERS.items())
def test_ptr_record(server_name, server):
    answer = query(server, "20.0.10.10.in-addr.arpa", "PTR")
    actual = {str(rdata.target).rstrip(".") for rdata in answer}

    assert actual == {"web.internal"}, (
        f"{server_name} ({server}) returned unexpected PTR records for 10.10.0.20: {actual}"
    )
