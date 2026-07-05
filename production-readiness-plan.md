# Parlez Production-Readiness Plan

Goal: make the application safe, reliable, and operationally ready for public deployment.

---

## Phase 1 — Security Hardening (blockers)

**Goal:** close the critical security gaps that make public deployment unsafe today.

### Tasks
1. Rotate exposed secrets
   - Revoke the existing `NVIDIA_API_KEY` shown in `.env` and generate a new one.
   - Generate a strong random `JWT_SECRET` via `openssl rand -hex 32`.
   - Ensure `.env` is in `.gitignore` and not tracked by git.
2. Strengthen auth
   - Increase minimum password length from 4 to 8 characters.
   - Add `secure=True, samesite='lax'` to the auth cookie (with a config flag for local HTTP dev).
   - Reduce JWT token expiry from 72 hours to a safer default (e.g., 24 hours) with refresh-token support if desired.
3. Add HTTPS path
   - Update `docker-compose.yml` to run behind a reverse proxy (Caddy or nginx) with automatic TLS.
   - Document local HTTPS dev setup.

### Verification
- `git log --all --full-history -- .env` shows no committed secrets.
- `python3 - <<'PY'` checks password length enforcement in `main.py`.
- Cookie `Set-Cookie` response headers include `Secure` and `SameSite=Lax` in production.
- Container boots with TLS and serves HTTPS.

---

## Phase 2 — Backend & Data Infrastructure

**Goal:** replace file-based storage and add production-grade protections.

### Tasks
1. Replace JSON file storage with SQLite
   - Add `sqlalchemy` / `databases` / `aiosqlite` to `requirements.txt`.
   - Migrate `Storage` class to use SQLite tables for users, conversations, comments, shares, and test results.
   - Provide a one-time migration script from `data/*.json` to SQLite.
2. Add rate limiting
   - Add `slowapi` to `requirements.txt`.
   - Apply per-IP and per-user rate limits to `/api/auth/*`, `/api/chat`, and `/api/exam/*`.
3. Add an API test suite
   - Add `pytest` and `httpx` test dependencies.
   - Write tests covering signup, login, JWT validation, chat, conversation CRUD, exam submission, and comments.
4. Add basic observability
   - Add structured request logging.
   - Add a `/health` endpoint and expose it outside auth.

### Verification
- `pytest` passes with ≥ 80% API coverage.
- `sqlite3 data/parlez.db .tables` shows migrated tables.
- Load test with `ab` or `locust` shows rate limits returning 429 after thresholds.
- `/health` returns 200 and includes DB connectivity status.

---

## Phase 3 — Reliability, Validation & Launch Prep

**Goal:** make the app resilient to failures and user abuse, then prepare for deployment.

### Tasks
1. AI provider resilience
   - Wrap `call_nvidia` with retries (3 attempts with exponential backoff).
   - Add a friendly user-facing message when the AI service is unavailable.
2. Input validation and sanitization
   - Validate uploaded file types and sizes in `/api/tts` and any ingest endpoints.
   - Escape all user-generated content rendered in HTML (chat messages, comments, shared titles).
3. Production deployment checklist
   - Add GitHub Action or pre-deploy script that runs tests, lint, and secret-scan.
   - Create a `README` deployment section covering env vars, TLS, backups, and upgrades.
   - Configure automated SQLite backups (e.g., nightly volume snapshot or `sqlite3 .backup`).

### Verification
- Simulate NVIDIA API failure (e.g., wrong key or blocked DNS); app returns a clean error message without crashing.
- Upload an oversized/invalid file and receive a 400 response.
- CI pipeline passes tests and `git-secrets`/`trufflehog` scan finds no exposed keys.
- Backup script runs successfully and produces a restorable SQLite file.

---

## Exit criteria for production

- [ ] No secrets in the repo; `.env` untracked.
- [ ] SQLite database in use; JSON storage deprecated.
- [ ] HTTPS/TLS configured.
- [ ] Rate limiting active.
- [ ] Auth cookies use `Secure` and `SameSite=Lax`.
- [ ] Test suite passes.
- [ ] `/health` endpoint live.
- [ ] AI failures handled gracefully.
- [ ] Backup and deployment docs written.
