"""
offboard_user.py

Disables an Entra ID user, revokes their active sessions, and removes them
from all group memberships. Every step is audit-logged.

Usage:
    python offboard_user.py --user-principal-name jdoe@contoso.onmicrosoft.com
"""

import argparse

from graph_client import GraphClient


def disable_user(client: GraphClient, upn: str) -> None:
    response = client.request("PATCH", f"/users/{upn}", json={"accountEnabled": False})
    response.raise_for_status()


def revoke_sessions(client: GraphClient, upn: str) -> None:
    response = client.request("POST", f"/users/{upn}/revokeSignInSessions")
    response.raise_for_status()


def get_group_memberships(client: GraphClient, upn: str) -> list[str]:
    response = client.request("GET", f"/users/{upn}/memberOf")
    response.raise_for_status()
    return [g["id"] for g in response.json().get("value", []) if g.get("@odata.type") == "#microsoft.graph.group"]


def remove_from_groups(client: GraphClient, upn: str, group_ids: list[str]) -> None:
    for group_id in group_ids:
        client.request("DELETE", f"/groups/{group_id}/members/{upn}/$ref")


def main():
    parser = argparse.ArgumentParser(description="Offboard an Entra ID user")
    parser.add_argument("--user-principal-name", required=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would happen without calling Microsoft Graph or writing any changes",
    )
    args = parser.parse_args()

    client = GraphClient(dry_run=args.dry_run)
    if args.dry_run:
        client.logger.info("Running in --dry-run mode — no changes will be made")
    upn = args.user_principal_name

    disable_user(client, upn)
    client.logger.info("Disabled account for %s", upn)

    revoke_sessions(client, upn)
    client.logger.info("Revoked active sessions for %s", upn)

    group_ids = get_group_memberships(client, upn)
    if group_ids:
        remove_from_groups(client, upn, group_ids)
        client.logger.info("Removed %s from groups: %s", upn, group_ids)
    else:
        client.logger.info("%s had no group memberships to remove", upn)


if __name__ == "__main__":
    main()
