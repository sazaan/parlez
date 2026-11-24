# Admin panel guide

Status: living document · updated 2026-11-23

## Access

The console is served at `ADMIN_PATH` (default `/parlez-admin`, configurable) and is also reachable at the friendly alias `/admin`. It is a separate credential from learner accounts:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD_HASH` (bcrypt; generate with `scripts/generate_admin_credentials.py`)
- `ADMIN_SESSION_SECRET` (≥32 characters)

If any is missing, every admin API fails closed with 503. The path itself is **not** a security control.

## Sign-in flow

1. `POST /api/admin/login` checks origin/same-site, then username (constant-time) and bcrypt password.
2. If TOTP MFA is enabled, a missing code returns 428; a wrong code returns 401.
3. A server-side `admin_sessions` row and a 15-minute JWT are created. The JWT is in an HttpOnly, SameSite=Strict cookie scoped to `/api/admin`.
4. Reads require a valid session; writes additionally require `X-CSRF-Token` from `GET /api/admin/session` and a same-origin `Origin`.
5. Failed logins and TOTP rejections are written to the durable `admin_audit` table (reason only — no passwords or codes).

## Tabs

| Tab | What it does |
| --- | --- |
| AI providers | See which providers have server keys, choose provider/model, run a mandatory connection test, save or roll back config. Keys never leave the server; provider URLs are fixed. |
| Course publishing | Per-level and per-module publish toggles, version-bound reviewer attestation, integrity checks before publishing. Publication gates learner APIs, not just menus. |
| Users | Paginated, privacy-limited directory (name, username, email, level, dates). No hashes or learning history. |
| Security | Enrol, replace, cancel or disable TOTP MFA. Any change revokes all admin sessions. |
| Sessions | List active admin sessions, revoke one or revoke all. |
| Observability | 30-second-polled sanitized metrics, SLOs, alerts, events and trace summaries. |
| Change log | Recent durable admin audit entries. |

## MFA recovery

MFA secrets are Fernet-encrypted with a key derived from `ADMIN_SESSION_SECRET`. Rotating that secret while MFA is enabled makes decryption fail closed (503) — there is no in-app recovery. Recovery requires server-side intervention: either restore the previous secret, or clear the stored MFA setting with a trusted script and re-enrol. **This is a known operational gap** — add a documented recovery script before relying on MFA in production.

## Known gaps

- Named admin accounts with roles now exist (`owner`, `editor`, `viewer`) under the **Accounts** tab or `/api/admin/accounts`. The env-configured account is seeded as owner; individual actions are attributed in the audit log. Role enforcement is present for account management; finer per-endpoint editor/viewer restrictions are a follow-up.
- No in-panel password rotation (edit `.env` and restart).
- Audit log is capped at 1000 rows; `GET /api/admin/audit?limit=&offset=&action=` now supports filtering and JSON export (a UI is still pending).
- MFA recovery: `python scripts/admin_recovery.py --status` shows stored MFA keys; `--confirm RESET-MFA` clears them, revokes admin sessions and writes an audit entry. Use only if MFA became undecryptable after a secret rotation, then re-enrol.
- Origin check depends on proxy headers; launch behind the provided Caddy configuration.
