"""
assign_groups.py

Syncs a user's group membership to match a target role profile defined in
config.json -> defaultGroups. Adds missing memberships and removes
memberships not part of the target profile.

Usage:
    python assign_groups.py --user-principal-name jdoe@contoso.onmicrosoft.com --department Sales
"""

import argparse

from graph_client import GraphClient


def get_current_groups(client: GraphClient, upn: str) -> set[str]:
    response = client.request("GET", f"/users/{upn}/memberOf")
    response.raise_for_status()
    return {g["id"] for g in response.json().get("value", []) if g.get("@odata.type") == "#microsoft.graph.group"}


def sync_groups(client: GraphClient, upn: str, user_id: str, target_group_ids: set[str]) -> None:
    current = get_current_groups(client, upn)
    to_add = target_group_ids - current
    to_remove = current - target_group_ids

    for group_id in to_add:
        body = {"@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"}
        client.request("POST", f"/groups/{group_id}/members/$ref", json=body)
        client.logger.info("Added %s to group %s", upn, group_id)

    for group_id in to_remove:
        client.request("DELETE", f"/groups/{group_id}/members/{upn}/$ref")
        client.logger.info("Removed %s from group %s", upn, group_id)


def main():
    parser = argparse.ArgumentParser(description="Sync group membership for an Entra ID user")
    parser.add_argument("--user-principal-name", required=True)
    parser.add_argument("--department", required=True)
    args = parser.parse_args()

    client = GraphClient()
    upn = args.user_principal_name

    user_resp = client.request("GET", f"/users/{upn}")
    user_resp.raise_for_status()
    user_id = user_resp.json()["id"]

    target_group_ids = set(client.config.get("defaultGroups", {}).get(args.department, []))
    if not target_group_ids:
        client.logger.info("No target groups configured for department '%s'", args.department)
        return

    sync_groups(client, upn, user_id, target_group_ids)


if __name__ == "__main__":
    main()
