# Remaining tasks — for future sessions

**Status snapshot:** 38 of 43 audit tasks complete (88%). 5 are blocked as
LARGE projects needing their own focused sessions; a few smaller items
were intentionally deferred from completed tasks and are documented
below. A pre-existing pytest issue (anyio.WouldBlock on 4 async tests)
was confirmed unrelated to my changes via `git stash`.

---

## 1. Blocked — LARGE / own-session work

These are scoped as separate projects because each is larger than a
single commit and benefits from a clean session with its own verification:

| # | Audit task | Why it's its own session |
|---|---|---|
| 3.10 | Raise test coverage to ≥80% | Each gap area needs its own test design + fixtures. Test for: XSS regression, comment/share IDOR, exam engine submit/grade, flashcard SM-2, content-ingest success, `data/parlez.db` untouched assertion. |
| 4.1 | Delete ~8k lines of dead code (`courses/a1_course_legacy.py`, `courses/a1.py`, `*.bak`, dead engine funcs, one-off scripts) | Risky without per-file `git grep "import <name>"` before each delete. Recommend checkpointed commits (one file per commit) with full pytest after each. Also unblocks tightening ruff to `ruff check .` (currently scoped to `main.py db.py engine migrate_to_sqlite.py`). |
| 4.9 | SSE streaming for chat (`/api/chat`) | Backend needs `StreamingResponse` wiring (TTS already has it as a reference). Frontend needs `EventSource` + error/timeout handling. Also unblocks `isGenerating = false` reset on stall. |
| 5.1 | a11y across 2300-line `static/app.js` | Convert clickable `<div>`s to `<button>`, add `aria-live="polite"` on chat output, modal focus trap + Esc, `prefers-reduced-motion`, visible focus outlines. Verify with Lighthouse. |
| 5.7 | Rewrite 5 stale doc files | `README.md` + `ARCHITECTURE.md` describe an "NVIDIA NIM media analyzer" that doesn't match reality. `COMPLETE_PROJECT_RECORD.md` says "JSON files" storage + "72h JWT" (actually SQLite + 24h). `VERCEL_DEPLOYMENT.md` is aspirational (no `vercel.json`, SQLite can't run serverless). Add new `CLAUDE.md` at the repo root capturing: real architecture, the "tests must use an isolated DB" rule, the "single SQLite worker" rule, and the "never commit `data/`/`books/`/`.env`" rule. |

---

## 2. Pre-existing test failures (anyio.WouldBlock)

These 4 tests fail with `anyio.WouldBlock` in `receive_nowait` (TestClient
async channel timeout):

- `tests/test_api.py::test_chat_mocked`
- `tests/test_api.py::test_exercise_check`
- `tests/test_security.py::test_chat_rejects_xss_payload`
- `tests/test_security.py::test_chat_detected_mode_still_french_focused`

**Diagnosis:** `git stash` of my recent edits reproduces the failures
unchanged — they pre-date my work. Likely an event-loop scope /
fixture-isolation issue in `conftest.py` interacting with
`pytest-asyncio` / `anyio` defaults.

**Repro:** `pytest tests/test_api.py::test_chat_mocked -q` → `E   anyio.WouldBlock`.

**Suspected fixes (in order of likelihood):**
1. Pin `anyio_backend = "asyncio"` via `pytest.ini` or `pyproject.toml` `[tool.pytest.ini_options]`.
2. Change `conftest.py` `client` fixture to use `with TestClient(main.app) as c:` (proper context-manager lifecycle).
3. Move `import main` out of `conftest.py` module-level and into the fixture, so storage init happens per-test.
4. Add `pytest-asyncio` `loop_scope` to match `slowapi`'s internal loop.

---

## 3. Deferred items inside completed tasks

These were intentionally not done as part of their parent task to keep
the commit focused. Each has a clear next step:

| Parent task | Deferred item | Where to pick up |
|---|---|---|
| 3.1 | Optimistic-lock `version` column on `User` (DB schema + `UPDATE … WHERE id=? AND version=?` retry on conflict) | `db.py` schema + `Storage.save_user`. The collapse-save + cap-test_results mitigations already cut the lost-update blast radius; this turns silent data loss into a detectable conflict. |
| 3.10 | Tests for the deletions made by 3.1, 3.6, 3.7, 3.9 (one regression test each) | `tests/test_api.py` — add before widening scope to the full 3.10 suite. |
| 5.4 | `feedbackHTML(correct, text)` helper exists but isn't called from existing sites (the pattern is "find existing div + toggle class", not "create new HTML") | Only worth refactoring if exercises get re-rendered from scratch (e.g., for offline mode). Skip for now. |
| 5.4 | Inline `style="…"` strings (audit counts ~133) → CSS classes | Search-and-replace pass against `static/app.js`. Mechanical but voluminous. |
| 5.4 | Wrap `app.js` in a module / split into files | Only worth doing alongside 5.1 (a11y) when the file is being touched anyway. |
| 3.6 | `pretty_print_explanation` style for the `explanation` field that's now sent back via the submit endpoints | Backend already returns it; ensure the frontend `data-action="check-exercise"` path renders it. |

---

## 4. Golden rules (memorize before touching this repo)

These are the rules the audit specifically called out, with current
status:

| Rule | Status |
|---|---|
| **Never run `pytest` against the real DB.** Tests use a `tempfile.mkdtemp()` SQLite via `conftest.py`'s `os.environ["DATABASE_URL"]` override set BEFORE `import main`. | Enforced (Task 1.4) |
| **The app uses SQLite. Do NOT run more than one server worker** (`--workers 1`). Comment at `main.py:1790` explains why (in-process storage + rate limiter). | Enforced (Task 3.2) |
| **Secrets live in `.env` (untracked).** `.gitignore` excludes it. `JWT_SECRET` MUST be ≥ 32 chars (app refuses to boot otherwise). | Enforced |
| **Never commit `data/`, `books/`, or `.env`.** All three are gitignored AND untracked-from-history via `git filter-repo` (Task 1.6). | Enforced (Task 1.2, 1.5, 1.6) |
| **CSP `script-src 'self'`** — no inline handlers, no inline scripts. `static/app.js` uses delegated listeners + `data-action`. | Enforced (Task 2.3) |
| **Frontend uses cookie-only auth.** Token is NOT in `localStorage`; the HttpOnly cookie is what carries the session. | Enforced (Task 2.2) |
| **`Dockerfile` runs as non-root `appuser`**, has `HEALTHCHECK`, expects single worker. | Enforced (Task 3.2) |
| **`.dockerignore` must keep `mock_tests/`** — `main.py` imports from it at runtime. The original Task 3.2 `.dockerignore` excluded it; that was fixed. Don't re-introduce. | Enforced |
| **`/api/upload` and `/api/knowledge` are gone.** Removed in Task 3.8/4.6 (the RAG feature was never queried by `/api/chat`). Don't re-add without also wiring chat to use it. | Removed |

---

## 5. Useful git references

| Look up | How |
|---|---|
| What I committed for a specific audit task | `git log --oneline --grep="Task <X.Y>"` |
| Exact code change for a task | `git show <commit>` |
| What was in the codebase before the audit | `git log --oneline` shows `fac8e28 Redesign landing phone mockup…` as the last commit before audit work started. Use `git show fac8e28^` to see the pre-audit `main.py`. |
| Backup before `git filter-repo` history rewrite | `/tmp/parlez-backup.git` (bare mirror). Still there. |
| Pre-audit (untracked) docs | `.kimchi/docs/verification.md`, `AUDIT_REPORT.md`, `COURSE_RESTRUCTURE_PLAN.md`, `docs/` — all untracked. |

---

## 6. Where things live in this session

- Working-tree changes (uncommitted): `static/landing.css` (pre-existing user work — DO NOT commit as part of audit fixes).
- All audit commits are on `main` and form a clean linear history from `fac8e28`.
- The `v1` branch is a pre-audit snapshot; it still references the old (now-rewritten) history. Re-clone if you need to compare against pre-audit state.
