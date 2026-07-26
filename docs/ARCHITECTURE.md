# Architecture

## Auth flow

App registration (client credentials) → `login.microsoftonline.com` token endpoint
→ access token scoped to `https://graph.microsoft.com/.default` → attached as
Bearer token to every Graph API call. No delegated/user sign-in involved, so
this is safe to run unattended (e.g. on a schedule).

## Components

- **graph_client.py / Connect-GraphApp.ps1** — auth + generic request wrapper + audit logging. Every other script depends on this.
- **onboard_user / Onboard-User** — user creation, temp password, group assignment.
- **offboard_user / Offboard-User** — disable account, revoke sessions, strip group memberships.
- **assign_groups / Assign-Groups** — diffs current vs. target group membership and reconciles.

## Audit logging

Every Graph call (success or failure) is written to `logs/audit.log` with
timestamp, action, target, and outcome. This directly maps to real IAM audit
requirements — a reviewer should be able to reconstruct "who did what to whom
and when" from the log alone.

## Design decisions / open questions (fill in as you build)

- [ ] Idempotency: what happens if onboarding runs twice for the same user?
- [ ] Error handling: retry policy for transient Graph API throttling (429s)?
- [ ] Secrets: client secret in config.json works for a dev tenant demo — note
      in the README that production would use a certificate or managed identity + Key Vault.
- [x] Testing: `--dry-run` flag added to the Python scripts (2026-07-25) — `GraphClient.request()`
      short-circuits and returns a synthetic response instead of calling Graph, so onboarding/
      offboarding/group-sync logic can be exercised end-to-end with zero risk to a real tenant.
      PowerShell parity is still open.
