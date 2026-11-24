# Parlez interactive curriculum — phase plan

Status: draft v1 · 2026-11-24 · owner direction: **start with the structural restructure** (interactive path + exam missions like Duolingo/Falou, web and mobile), then layer content and AI.

## Why this order

The current app is a chat window plus a set of tool panels. That cannot host a lesson "session" (ordered steps, immediate feedback, progression, replay) or exam tasks with timing. The single biggest restructuring is therefore a dedicated **learning shell** that can host both ordinary lessons and exam missions. Build it first; content and AI plug into it afterwards.

## Phase A — Learning shell (start here)

Goal: a mobile-first "Learn" home with a visible path of units/lessons and a repeatable session player.

- A1. Path view: units → lesson nodes, locked/current/completed states, progress summary, deep links.
- A2. Session state machine: intro → vocabulary → grammar → dialogue → exercises → results, with resume-on-reload.
- A3. Exercise player: multiple-choice, fill-blank, translate, reorder, matching, dictation; immediate explanatory feedback; keyboard and touch support.
- A4. Results + XP: completion persisted to `/api/progress/complete-lesson`, mascot reaction, streak/XP display.
- A5. Responsive 360px → desktop, reduced-motion and screen-reader support.

Uses the existing `/api/courses/{level}`, `/api/courses/{level}/lessons/{id}` and progress APIs — no content rewrite required.

**Design decisions from research (2026-11-24):**
- Single vertical winding path of unit ribbons + lesson nodes; node icons signal type (book, ✏️, 🎧, 🎯 exam). Units are labelled by communicative outcome.
- Session state machine: `BRIEFING → PRESENTING → AWAITING_ANSWER → CHECKING → FEEDBACK → (EXPLAIN overlay) → NEXT → … → MISTAKE_REVIEW → RESULTS`.
- Answer feedback is immediate (✓/✗ + short explanation); mistakes are queued and replayed later in the same session. Prefer Duolingo's forgiving "energy" idea over punishing hearts; never gate learning behind a consumable, ads, or paywall.
- Reuse the existing XSS-safe `renderExercise()` and its 13 exercise types. Add a registry later; do not fork the renderer.
- Keyboard + touch: tap-to-answer, ≥44px targets, 16px inputs (no iOS zoom), progress bar at top, bottom-anchored action bar on mobile; desktop caps the lesson column (~720px).
- CSS-only motion (mascot pop, progress fill, feedback slide-up) with `prefers-reduced-motion` and explicit text/icon equivalents. `aria-live` for feedback; focus moves to Continue; overlays trap focus and return it.
- "Explain My Answer" is a thin inline overlay backed by the existing tutor, free and never interrupting the loop.
- Exam missions are nodes/missions in the same shell (timed chrome + honest labels), not a separate app.

## Phase B — Exam missions inside the shell ✅ SHIPPED 2026-11-24

Delivered: exam mission cards in the path; briefing with official-sample links; timed reading/listening missions using **original** items from `mock_tests/original_items.py`; server-side grading with per-item explanations and spec sources; licence-aware resource registry at `/api/practice/resources` shown in the mission UI. No real past questions are reproduced — see `docs/SOURCE_REGISTER.md` §0/§3c. Writing/speaking task players remain for a later increment.

- B1. Exam mission cards in the path (TCF/TEF streams) with honest "original practice, not official" labels.
- B2. Timed listening/reading item player: audio-once rules, question navigator, review screen with explanations.
- B3. Writing task player: word counts, timers, self-check rubric and optional AI feedback.
- B4. Speaking task player: role-play prompts, recording/transcript, unofficial self-review.
- B5. Versioned format facts from `/api/exam/formats`, `verified_on` dates and source links.

## Phase C — AI tutor inside the session

- C1. Contextual "Ask Pip" panel seeded with the current lesson/exam task.
- C2. Hint and explanation requests that never give away the assessed answer.
- C3. Post-session conversation mission with transcript and feedback.
- C4. Guardrails: no raw exam answers, no score prediction, moderation on output.

## Phase D — Content at scale (real materials, attributed)

- D1. Resource register: publisher series and open/licensed materials with exact reuse terms.
- D2. Authoring templates derived from real course patterns (Inspire/Édito/Cosmopolite/etc.) with provenance fields.
- D3. A1 → A2 → B1 → B2 unit authoring, level by level.
- D4. Original TEF/TCF item banks modelled on official task specs; official samples linked, never copied.
- D5. Qualified review, versioning, pilot and claims register.

## Phase E — Motivation, polish and growth

- E1. Streaks/freezes/badges surfaced in the path, leagues optional.
- E2. Mascot states, celebrations, motion with reduced-motion fallback.
- E3. Sharing cards, referrals, SEO guide and community loops.

## Content standard (researched 2026-11-24)

- **32 units total**: 8 per level (A1→B2), each ending in a concrete task/défi; a four-skill check every second unit and a full practice épreuve blanche at level end.
- A1 sequence (survival/identity): greetings → identity → family → home → food/café → daily routine → invitations → A1 bilan.
- A2: past narration → travel → housing → health → work → consumer rights → media → A2 bilan.
- B1: community rules → memory/narration → work → travel hypotheses → media critique → explaining knowledge → cultural mediation → B1 bilan.
- B2: opinion essay → synthesis → professional case → prospective dossier → cultural review → advocacy brief → intercultural debate → B2 bilan.
- Every unit follows the publisher-derived skeleton: contract → input → comprehension → grammar discovery → vocabulary + phonology → culture → drills → mediation → final task → bilan.
- Build from **CC BY** open resources first; cite exactly. Publisher books are structural references only.

## Exam prep — "real past questions" policy

**We will not reproduce real/past TEF or TCF questions**, because CCI/FEI own them and Canadian/French copyright law does not allow it in a commercial product (research: `docs/SOURCE_REGISTER.md` §0). Instead:
- write original items from the published specs (TEF: 40Q/60min reading, 40Q/40min listening played once, 2 writing tasks 80/200 words, 2 speaking tasks 5+10min; TCF: 39Q/60min reading, 39Q/35min listening once, 3 writing tasks 60–120/120–150/120–180 words, 3 speaking tasks over 12min);
- link to official sample PDFs/audio with attribution;
- display a permanent "independent, unofficial practice — not an official score" disclosure;
- never show a /699 or NCLC score for a practice set.

## Definition of done for a phase

Working on web + mobile, tests green, no regression to auth/security, `progress.html` updated, and a short note in this file describing what shipped.
