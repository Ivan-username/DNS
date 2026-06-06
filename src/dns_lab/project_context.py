"""Machine-readable context for Task 01.

Task 01 is a context and architecture milestone. It does not create the
Docker Compose or BIND9 runtime configuration; those belong to later tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network, ip_address, ip_network


@dataclass(frozen=True)
class HostAddress:
    """Named host planned for the future DNS lab."""

    name: str
    address: IPv4Address
    role: str


@dataclass(frozen=True)
class TaskOwner:
    """Recommended ownership for the remaining autonomous tasks."""

    participant: str
    task_files: tuple[str, ...]
    responsibility: str


@dataclass(frozen=True)
class ProjectContext:
    """Accepted project decisions that later implementation should reuse."""

    primary_dns_implementation: str
    unbound_role: str
    base_domain: str
    docker_network: IPv4Network
    reverse_zone: str
    master_dns: HostAddress
    slave_dns: HostAddress
    example_hosts: tuple[HostAddress, ...]
    required_features: tuple[str, ...]
    task_sequence: tuple[str, ...]
    recommended_owners: tuple[TaskOwner, ...]
    task_01_excluded_outputs: tuple[str, ...]


PROJECT_CONTEXT = ProjectContext(
    primary_dns_implementation="BIND9",
    unbound_role="Unbound documentation-only alternative recursive resolver",
    base_domain="internal",
    docker_network=ip_network("10.10.0.0/24"),
    reverse_zone="0.10.10.in-addr.arpa",
    master_dns=HostAddress(
        name="dns-master",
        address=ip_address("10.10.0.2"),
        role="BIND9 master authoritative and recursive DNS",
    ),
    slave_dns=HostAddress(
        name="dns-slave",
        address=ip_address("10.10.0.3"),
        role="BIND9 slave authoritative DNS",
    ),
    example_hosts=(
        HostAddress("web.internal", ip_address("10.10.0.20"), "example web service"),
        HostAddress("api.internal", ip_address("10.10.0.21"), "example API service"),
        HostAddress("mail.internal", ip_address("10.10.0.30"), "example mail service"),
    ),
    required_features=(
        "authoritative forward zone",
        "authoritative reverse zone",
        "trusted-client recursion ACL",
        "DNSSEC validation",
        "BIND logging block",
        "master to slave zone transfer",
        "Split-Horizon through BIND views",
        "rndc control",
        "Response Rate Limiting",
        "automated record and latency tests",
        "README and demo scenario",
    ),
    task_sequence=(
        ".ai/tasks/task-01.md",
        ".ai/tasks/task-02-infrastructure-master.md",
        ".ai/tasks/task-03-slave-security.md",
        ".ai/tasks/task-04-tests-docs-demo.md",
    ),
    recommended_owners=(
        TaskOwner(
            participant="participant-1",
            task_files=(".ai/tasks/task-02-infrastructure-master.md",),
            responsibility="Docker Compose, master DNS, zones, logging, rndc, base README",
        ),
        TaskOwner(
            participant="participant-2",
            task_files=(
                ".ai/tasks/task-03-slave-security.md",
                ".ai/tasks/task-04-tests-docs-demo.md",
            ),
            responsibility="slave DNS, security, Split-Horizon, RRL, tests, docs, demo",
        ),
    ),
    task_01_excluded_outputs=(
        "docker-compose.yml",
        "master/",
        "slave/",
        "tests/",
        "README.md",
    ),
)


def validate_project_context(context: ProjectContext = PROJECT_CONTEXT) -> list[str]:
    """Return validation errors for the Task 01 source-side context."""

    errors: list[str] = []

    if context.primary_dns_implementation != "BIND9":
        errors.append("Primary DNS implementation must remain BIND9.")

    if context.base_domain != "internal":
        errors.append("Base domain must remain internal.")

    if context.docker_network != ip_network("10.10.0.0/24"):
        errors.append("Docker network must remain 10.10.0.0/24.")

    if context.master_dns.address != ip_address("10.10.0.2"):
        errors.append("Master DNS address must remain 10.10.0.2.")

    if context.slave_dns.address != ip_address("10.10.0.3"):
        errors.append("Slave DNS address must remain 10.10.0.3.")

    if context.reverse_zone != "0.10.10.in-addr.arpa":
        errors.append("Reverse zone must remain 0.10.10.in-addr.arpa.")

    planned_addresses = [context.master_dns.address, context.slave_dns.address]
    planned_addresses.extend(host.address for host in context.example_hosts)
    for address in planned_addresses:
        if address not in context.docker_network:
            errors.append(f"{address} is outside {context.docker_network}.")

    unbound_role = context.unbound_role.lower()
    if "unbound" not in unbound_role or "alternative" not in unbound_role:
        errors.append("Unbound must stay documented as an alternative, not implemented.")

    if len(context.task_sequence) != 4:
        errors.append("Task sequence must keep four autonomous task files.")

    if not context.recommended_owners:
        errors.append("Recommended two-person ownership must be present.")

    return errors
