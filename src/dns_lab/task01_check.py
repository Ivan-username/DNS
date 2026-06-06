"""CLI self-check for the Task 01 source-side project context."""

from __future__ import annotations

from .project_context import PROJECT_CONTEXT, validate_project_context


def main() -> int:
    errors = validate_project_context(PROJECT_CONTEXT)
    if errors:
        print("Task 01 context check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Task 01 context check passed.")
    print(f"Primary DNS implementation: {PROJECT_CONTEXT.primary_dns_implementation}")
    print(f"Base domain: {PROJECT_CONTEXT.base_domain}")
    print(f"Docker network: {PROJECT_CONTEXT.docker_network}")
    print(f"Master DNS: {PROJECT_CONTEXT.master_dns.address}")
    print(f"Slave DNS: {PROJECT_CONTEXT.slave_dns.address}")
    print(f"Reverse zone: {PROJECT_CONTEXT.reverse_zone}")
    print("Task 01 deliberately excludes runtime DNS infrastructure files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
