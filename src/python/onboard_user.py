"""
onboard_user.py

Creates a new Entra ID user and assigns them to the groups mapped to their
department, as defined in config.json -> defaultGroups.

Usage:
    python onboard_user.py --user-principal-name jdoe@contoso.onmicrosoft.com \
        --display-name "Jane Doe" --department Engineering
"""

import argparse
import secrets
import string

from graph_client import GraphClient


def generate_temp_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_user(client: GraphClient, upn: str, display_name: str) -> dict:
    body = {
        "accountEnabled": True,
        "displayName": display_name,
        "mailNickname": upn.split("@")[0],
        "userPrincipalName": upn,
        "passwordProfile": {
            "forceChangePasswordNextSignIn": True,
            "password": generate_temp_password(),
        },
    }
    response = client.request("POST", "/users", json=body)
    response.raise_for_status()
    return response.json()


def assign_to_groups(client: GraphClient, user_id: str, group_ids: list[str]) -> None:
    for group_id in group_ids:
        body = {"@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"}
        client.request("POST", f"/groups/{group_id}/members/$ref", json=body)


def main():
    parser = argparse.ArgumentParser(description="Onboard a new Entra ID user")
    parser.add_argument("--user-principal-name", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--department", required=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would happen without calling Microsoft Graph or writing any changes",
    )
    args = parser.parse_args()

    client = GraphClient(dry_run=args.dry_run)
    if args.dry_run:
        client.logger.info("Running in --dry-run mode — no changes will be made")

    group_ids = client.config.get("defaultGroups", {}).get(args.department, [])
    if not group_ids:
        client.logger.info("No groups mapped for department '%s' — skipping group assignment", args.department)

    user = create_user(client, args.user_principal_name, args.display_name)
    client.logger.info("Created user %s (id=%s)", args.user_principal_name, user["id"])

    if group_ids:
        assign_to_groups(client, user["id"], group_ids)
        client.logger.info("Assigned %s to groups: %s", args.user_principal_name, group_ids)


if __name__ == "__main__":
    main()
