# Parlez design system

Status: living document · updated 2026-11-23

## Adapted from Newa Bhaye (2026-11-24)

Side-by-side review of `../NewaBhaye` screens and styles identified these concrete improvements, now ported to Parlez:

- **Topbar stat pills** (streak, XP) and an avatar button, with a matching color treatment.
- **Learn home greeting** with time-of-day salutation and learner name.
- **Continue hero** featuring the next lesson, a primary CTA, mixed-review secondary action and Pip art.
- **Daily goal strip** with a conic-gradient progress ring, meter, streak and streak-freeze status.
- **Quick cards** (Mixed review, Level check, Word of the day) using the same card component as Practice.
- **Word-of-the-day card** populated from `/api/practice/word-of-day`.
- **"Your path" header with progress count**, unit badges, `done/total` counters and per-unit progress meters.
- **Lesson feedback polish**: combo counter and subtle Web Audio tones for correct/incorrect answers; the existing mascot celebration, confetti and unlock animations remain.

## Sidebar reopen & loading mascot (2026-11-24)

When the desktop sidebar collapses, a persistent `»` rail button appears at the left edge to reopen it (alongside the header hamburger and the in-sidebar `«` button). The state is mirrored on `#appContainer` so the rail can be shown purely with CSS. The "New Chat" control was redesigned as a full-width gradient card with a＋icon and a clearer "New conversation" label, instead of a cramped pill squeezed next to the logo.

Section switches now show a centered Pip loader (bouncing mascot, message and animated dots) while data is fetched — Learn, Practice, Rewards, Exam formats, lessons, placement and exam missions all use it, with a small minimum display time so fast transitions still feel smooth.

## Collapsible sidebar (2026-11-24)

The sidebar can be collapsed on desktop with either the header hamburger or the new `«` button in the sidebar header (`»` expands). The state is saved in `localStorage` so it survives reloads. On tablets/phones the same control opens the sidebar as a slide-over with a backdrop; it closes on backdrop click, Escape, resize, or after choosing a destination. CSS uses `transform` for the mobile drawer and animated width/margin for desktop collapse.

## Navigation consolidation (2026-11-24)

One sidebar component (`.sidebar-nav-link`) is used for every destination: Courses & Path, Practice, Speaking, AI Tutor (opens chat), Rewards, My Progress, Level check and the Mock Tests group placed directly below Level check. Redundant sections — the old separate Courses tool, Practice Scenarios, Quick Practice and Content Tools — were removed. Practice now opens a single hub containing both conversation scenarios and quick drills, using the same card component throughout. The mobile bottom nav mirrors the same destinations.

## Visual refresh (2026-11-24)

Reference apps studied: **Newa Bhaye** (warm cream gradients, dotted texture, mascot Diyo, top stat pills, bottom nav, confetti), **Duolingo** (single clear path, tactile oversized options, instant feedback, streak/XP HUD), **Falou** (short speaking-first missions, listen → repeat → playback). Applied in `static/parlez-polish.css` (loaded last so it overrides legacy tokens):

- warm cream/saffron/wine palette, radial gradient washes and subtle dotted texture;
- glass sidebar/topbar, rounded cards, deeper layered shadows;
- global mobile bottom nav (Path / Practice / Speak / Tutor / Rewards) with an active pill;
- larger tactile exercise options with hover/press/correct/incorrect animation;
- Pip mascot on login, welcome, sessions and results with float/jump states;
- confetti on lesson completion; `prefers-reduced-motion` disables all of it.

**Bug fixed:** the Learn view stayed visible when opening Chat/Tool views, pushing chat halfway down the page. View switches now hide all other primary views.

## Principles

1. **Calm, not loud.** Ivory paper, wine, gold and sage — a study space, not a casino.
2. **Outcome-led copy.** Say what the learner can do, not how settings are synchronized.
3. **Honest by default.** Practice labels are not certification; never imply official exam scores or immigration outcomes.
4. **Motion has meaning.** Animate feedback, progress and state changes; respect `prefers-reduced-motion`.

## Tokens

Defined in `static/landing.css` (`:root`) and mirrored in `static/styles.css` / `static/app-theme.css`.

| Token | Value | Use |
| --- | --- | --- |
| `--paper` / `--paper-deep` | `#FBF8F3` / `#F4EEE4` | Page backgrounds |
| `--card` | `#FFFDFA` | Cards, panels |
| `--ink` / `--ink-soft` / `--ink-muted` | `#1D1815` / `#4A423C` / `#6F645B` | Text hierarchy |
| `--wine` / `--wine-deep` / `--wine-ink` | `#7C2D3F` / `#5E2130` / `#3E1620` | Brand, primary buttons, headers |
| `--gold` / `--gold-soft` | `#C0934A` / `#E9CD97` | Accents, highlights, mascot beak |
| `--sage` | `#6E8574` | Success / secondary accents |
| `--radius` / `--radius-lg` | `18px` / `26px` | Card and panel rounding |
| `--font-display` | Fraunces, Playfair Display, Georgia | Headlines |
| `--font-sans` | Inter, system stack | UI and body |

> The two CSS files still duplicate some tokens with different names. Consolidation is a follow-up; do not introduce a *third* naming scheme.

## Mascot — Pip

- Asset: `static/mascot.svg` (original Parlez parrot, brand palette).
- Usage: hero (`static/landing.html`), app welcome (`static/app.js` `welcomeHTML()` and `static/index.html`), share card (`static/og-card.svg`).
- Meaning: a friendly study companion who gives feedback a face. The XP update path adds `.mascot-celebrate` for a short pop animation.
- Rules: keep the silhouette and 2–3 colour palette consistent; no imitations of other apps' characters; always `aria-hidden`/empty `alt` when decorative.

## Motion

- Native CSS animations only; no animation library dependency.
- `mascot-float` (landing), `mascot-bob` + `mascot-pop` (app), marquee, reveal-on-scroll, reading-progress bar.
- Every decorative animation must be disabled under `@media (prefers-reduced-motion: reduce)`.
- Prefer `transform` and `opacity`; avoid layout-triggering properties.

## Components

- **Buttons**: `btn-solid` (primary), `btn-outline`, `btn-quiet`, `btn-gold`; `btn-block` for full-width pricing CTAs.
- **Confirmations**: `confirmDialog()` in `static/app.js` — accessible in-app replacement for `confirm()`, with Escape/backdrop dismissal and focus on the destructive action.
- **Landing sections**: navbar, hero + app window, trust bar, marquee, How it works, features bento, About/pathways, pricing, CTA, collapsible footer disclosures.
