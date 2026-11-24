# Claims register

Status: living document · 2026-11-24 · every public claim must have evidence here or be removed.

| Public claim | Where | Evidence / source | Allowed wording |
| --- | --- | --- | --- |
| A1–B2 practice pathways | landing, Learn path | `courses/attributed_content.py` (32 units / 96 lessons), validated by `courses/validation.py` | "practice pathways labelled A1–B2" |
| Built from published, attributed materials | `/legal`, landing | `docs/SOURCE_REGISTER.md` §3b/§3c | "curriculum authored from published French-learning materials, with attribution" |
| AI assists explanations and feedback | `/legal` | `engine/rewards.py`, chat/writing endpoints; moderation in `engine/moderation.py` | "AI assists explanations and conversation practice" |
| Not CEFR/NCLC certification | landing, `/legal`, Learn path | `docs/CURRICULUM_REDESIGN.md`, `docs/SOURCE_REGISTER.md` §0 | "practice labels, not certification" |
| A2–B2 published without reviewer attestation | landing, course API | `PROVENANCE.review_state = "practice"` | state it plainly, never imply reviewed |
| TEF/TCF-style original practice | exam missions | `mock_tests/original_items.py`, `mock_tests/formats.py` | "original items modelled on published task specifications" |
| Official samples linked for reference | exam mission UI | `mock_tests/resources.py` | "official samples open on the test owner's site" |
| No official score or immigration outcome | everywhere | `static/legal.html`, `static/guide.html` | "practice accuracy only; not an official score" |
| Two years' validity for official results | free guide | IRCC language testing page | "verify current rules at canada.ca" |
| CRS points for French | free guide | IRCC / francophone immigration pages | "can add points depending on your full profile" |

**Forbidden until proven:** "official mock exam", "real past questions", "CEFR-certified", "NCLC 7 guaranteed", "accepted by IRCC", "endorsed by CCI/FEI/TV5MONDE", "all courses written by AI".

**Review gate (D5):** before promoting any unit from `practice` to `reviewed`, record reviewer name, credentials, date, content version and changes required in `ContentProvenance`; independently benchmark a sample of tasks; keep a pilot evidence file. No reviewer is recorded yet — all 32 units remain `practice`.
