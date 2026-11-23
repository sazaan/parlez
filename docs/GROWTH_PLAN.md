# Parlez growth plan

Status: living document · updated 2026-11-23 · aligned with `progress.html` P9.

## Positioning

"The French you need for Canada PR — built for Nepali speakers." Lead with the learner's goal (CRS points and four-skill French), then the A1–B2 path mapped to TEF/TCF formats, then speaking practice, then Nepal-friendly access. Every claim must match `static/legal.html`: no certification, no score or PR guarantee, no affiliation.

## Channels

1. **Free content/SEO.** The first asset is `/learn/french-for-canada`. Next: NCLC 7 vocabulary by theme, "is Duolingo enough for TEF?", TEF score-column guide, French for appointments/interviews, and short Nepali + English versions. Use FAQ/HowTo structured data and fast static pages.
2. **Mascot-led social.** Pip reacts to CRS draw news, celebrates streaks and posts a weekly "French phrase for your PR interview". Reuse the same character across app, landing and social (see `docs/DESIGN_SYSTEM.md`).
3. **Partnerships.** Alliance Française de Katmandou (official exam centre) for co-branded prep funnels and referrals; migration consultants and study-abroad agents; colleges/French departments; Canadian Nepali associations for beta testers. Never describe a partner's review as an endorsement or certification.
4. **Lifecycle & referrals.** Signup supports `?ref=CODE`; `/api/referrals/me` exposes a code and link; a referred learner completing their first lesson grants the referrer a lesson-completion reward once. Next: activation emails, streak-rescue nudges and annual-plan emphasis when payments launch.
5. **Measurement.** Privacy-safe events already emitted server-side: signup, lesson completion, chat, exam practice, reward events, payment state transitions (when enabled). Next: signup → first lesson → first speaking → paid funnel reporting and an A/B cadence. Keep a claims register; never A/B away the learning mission.

## Guardrails

- No fabricated learner counts or testimonials.
- No "official", "certified" or "guaranteed" language unless a real, verifiable basis exists.
- Honest course-status labels (practice / reviewed) and visible disclaimers.
- Partnerships and affiliate arrangements must be disclosed.
