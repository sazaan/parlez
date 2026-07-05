# Parlez Production-Readiness Plan

Goal: make the application safe, reliable, and operationally ready for public deployment.

---

## Completed Work

The following work has been completed since this plan was first written.

### UI/UX

- **Landing page** (`static/landing.html`, `static/landing.css`)
  - Public landing page served at `/` with hero, features, about, footer.
  - Premium glassmorphism hero with floating phone mockup, editorial serif typography, and responsive nav.
  - The existing auth screen is now served at `/login`.
- **Premium visual refresh** (`static/styles.css`, `static/index.html`, `static/app.js`)
  - Upgraded CSS design system: refined palette, spacing scale, shadow scale, border-radius tokens, transitions.
  - Glassmorphism auth card, sidebar, main header, and input area.
  - Gradient buttons and focus rings.
  - Premium cards for quiz, exercise, flashcards, tests, comments, and vocabulary.
  - Fade-in animations, hover lift effects, and smooth micro-interactions.
  - Improved welcome screen, empty states, and chat bubbles.
- **Mock-test pause/resume** (`static/app.js`, `static/styles.css`)
  - Pause/resume controls and auto-pause on tab switch with a frosted overlay.
- **Sidebar UX** (`static/index.html`, `static/styles.css`)
  - Sidebar sections collapsed by default.

### Security

- **Auth hardening**
  - Minimum password length increased to 8 characters.
  - `JWT_SECRET` must be ≥ 32 characters or the app refuses to start.
  - Auth cookies use `Secure` and `SameSite=Lax` (configurable via `COOKIE_SECURE` / `COOKIE_SAMESITE`).
  - JWT token expiry is configurable via `TOKEN_EXPIRY_HOURS`.
- **Input validation**
  - File upload validation for type, extension, and 10 MB size limit.
  - User-generated content (chat messages, comments, shared titles) is escaped before DOM insertion.
- **Secrets handling**
  - `.env` is in `.gitignore`.
  - `.env.example` documents required variables.

### Backend & Data

- **SQLite storage** (`db.py`, `migrate_to_sqlite.py`)
  - Replaced JSON file storage with SQLite using SQLAlchemy.
  - Users, shared links, and comments stored as JSON columns for minimal endpoint rewrites.
  - WAL mode enabled for durability and concurrent readers.
  - One-time migration script from legacy `data/*.json` files.
- **Stateless storage refactor** (`db.py`, `main.py`)
  - Removed in-memory caches so multiple Uvicorn workers share consistent state.
  - Added `DATABASE_URL` environment support for SQLite and PostgreSQL.
  - Updated `migrate_to_sqlite.py` and `backup.py` to use the new stateless API.
- **Rate limiting** (`main.py`)
  - `slowapi` per-IP limits on auth, chat, and exam endpoints.
- **API test suite** (`tests/`)
  - `pytest` tests covering signup/login, conversations, chat, exercises, flashcards, comments, sharing, export, progress, and landing routes.
- **Observability**
  - Structured request logging to stdout.
  - `/health` endpoint that checks database connectivity.
- **Graceful shutdown** (`main.py`)
  - FastAPI lifespan handler closes the database engine cleanly on shutdown.

### Reliability & Operations

- **AI provider resilience**
  - `call_nvidia` retries with exponential backoff and returns friendly errors on 503/timeout.
- **TTS performance** (`main.py`)
  - Concurrent chunk downloads and streaming response reduce perceived latency.
- **Backup** (`backup.py`)
  - Automated SQLite online-backup script with retention policy.
- **CI/CD** (`.github/workflows/ci.yml`)
  - GitHub Actions workflow runs ruff lint, pytest, and TruffleHog secret scan.
- **Deployment docs**
  - `DEPLOYMENT.md` covers env vars, TLS, backups, and upgrades.
  - `docker-compose.prod.yml` + Caddyfile for HTTPS reverse proxy.

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

- [x] No secrets in the repo; `.env` untracked.
- [x] SQLite database in use; JSON storage deprecated.
- [x] HTTPS/TLS configured.
- [x] Rate limiting active.
- [x] Auth cookies use `Secure` and `SameSite=Lax`.
- [x] Test suite passes.
- [x] `/health` endpoint live.
- [x] AI failures handled gracefully.
- [x] Backup and deployment docs written.

## Remaining blocker before public deployment

- [ ] **Rotate the exposed `NVIDIA_API_KEY`** in `.env` and revoke the old key in the NVIDIA dashboard.
  - This must be done by the project owner; no code changes are required.
  - After rotation, verify the `/api/chat` endpoint still returns AI responses.

## Current test & lint status

- `venv/bin/ruff check main.py db.py migrate_to_sqlite.py backup.py tests/conftest.py tests/test_api.py tests/test_landing.py` → clean
- `JWT_SECRET=$(openssl rand -hex 32) NVIDIA_API_KEY=dummy venv/bin/python -m pytest tests/ -q` → 15 passed
- `venv/bin/python backup.py --dest /tmp/parlez-backup-test --keep 3` → backup created successfully
