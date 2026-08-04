# Entra ID Automation Toolkit

Automated User Lifecycle Manager — a PowerShell/Python toolkit that automates user
onboarding/offboarding, group assignment, and audit logging against a Microsoft
Entra ID (Azure AD) tenant using the Microsoft Graph API.

Built as a portfolio project for the IAM Developer path, on top of hands-on
Entra ID experience (app registrations, Conditional Access, PIM, identity
governance) and working toward the SC-300 certification.

## What it does

- **Onboarding**: creates a new user, assigns licenses, adds to department/role groups
- **Offboarding**: disables the account, revokes sessions, removes group memberships, archives the audit trail
- **Group assignment**: syncs a user's group membership to match a target role profile
- **Audit logging**: every action is logged locally (and optionally pushed to a log file / SIEM-friendly format) with timestamp, actor, target user, and outcome

## Auth model

Uses the OAuth 2.0 **client credentials flow** (app-only permissions) against an
app registration in a free Microsoft 365 Developer Program tenant. No user
interaction required — suitable for a scheduled/unattended script.

Required Graph API application permissions (admin consent required):
- `User.ReadWrite.All`
- `Group.ReadWrite.All`
- `AuditLog.Read.All` (optional, for pulling native Entra audit events)

## Project layout

```
entra-id-automation-toolkit/
├── config/
│   └── config.example.json   # copy to config.json, fill in tenant/app details — never commit config.json
├── src/
│   ├── python/
│   │   ├── graph_client.py       # auth + token acquisition (msal) + generic Graph request helper
│   │   ├── onboard_user.py
│   │   ├── offboard_user.py
│   │   └── assign_groups.py
│   └── powershell/
│       ├── Connect-GraphApp.ps1  # auth via Microsoft Graph PowerShell SDK, app-only
│       ├── Onboard-User.ps1
│       ├── Offboard-User.ps1
│       └── Assign-Groups.ps1
├── logs/                      # audit log output (gitignored)
└── docs/
    └── ARCHITECTURE.md
```

## Setup

1. Register an app in your dev tenant (Entra admin center → App registrations), grant
   the API permissions above, create a client secret.
2. `cp config/config.example.json config/config.json` and fill in `tenantId`,
   `clientId`, `clientSecret`.
3. Python: `pip install -r requirements.txt`
4. PowerShell: `Install-Module Microsoft.Graph -Scope CurrentUser`

## Usage

```bash
python src/python/onboard_user.py --user-principal-name jdoe@contoso.onmicrosoft.com --department Engineering
```

```powershell
./src/powershell/Onboard-User.ps1 -UserPrincipalName jdoe@contoso.onmicrosoft.com -Department Engineering
```

## Status

Scaffold only — implementation in progress.
