# Privacy-safe measurement & experiments

Status: living document · 2026-11-24

## What is recorded

`POST /api/events` accepts only an allow-listed event name and a small property whitelist (`level`, `exam`, `skill`, `variant`, `source`). **No learner text, answers, chat messages or free-form fields are stored.** Events are written to `learning_events`.

| Event | Fired from | Meaning |
| --- | --- | --- |
| `lesson_start` | Learn session player | learner opened a lesson |
| `lesson_complete` | Learn session results | lesson finished |
| `exam_mission_start` / `exam_mission_submit` | exam mission | practice mission started/submitted |
| `placement_submit` | informal level check | level check submitted |
| `coach_request` | Ask Pip / coach card | explanation requested |
| `share_progress` | results share card | progress shared |

Funnel totals are available to admins at `GET /api/admin/metrics/funnel`. The aggregate answers: signup → first lesson → first speaking → paid once payment entitlements are live.

## A/B tests

`GET /api/experiments/{key}` returns a stable deterministic variant (`control` or `variant`) per user. Assignment is stored in `experiment_assignments` so it never flips between sessions. Start with non-content changes (button labels, CTA order); never A/B away the learning mission or hide explanations.

## Rules

1. Measurement must never block learning — client emits are fire-and-forget.
2. No PII, message text, answer text or IP is stored in learning events.
3. Report cohorts in aggregate; do not expose per-learner funnels in the admin UI.
4. Any new event name must be added to the backend allow-list; unknown names are rejected with 400.
