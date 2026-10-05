# PARLEZ
## Affordable French learning, with a path toward TEF Canada and TCF Canada preparation

**Project description · market evidence · product strategy · technical architecture · commercial feasibility**  
**Prepared:** 5 October 2026 · **Version:** 1.0  
**Pricing assumption:** US$4.99 per month, before applicable taxes.  
**Status:** Existing prototype; proposed paid product and expansion roadmap.

> **Mission:** Make structured French learning and consistent, personalized practice accessible to learners who cannot afford frequent private tuition—starting with people pursuing Canadian immigration goals.

### Document conventions

**Implemented** means observed in the repository, not independently certified or production-load-tested. **Proposed** means a recommendation, not an available feature. **Estimate** means an explicit planning assumption rather than measured customer behavior. Immigration rules, provider availability, and prices must be rechecked before launch. This document is educational and commercial research, not immigration or legal advice.

---

## Executive summary

Parlez is a French-learning web application combining a familiar, ChatGPT-style conversation interface with structured lessons, practice exercises, spaced-repetition flashcards, writing feedback, and test-practice workflows. Its intended launch curriculum is **A1–B2**, organized around the Common European Framework of Reference for Languages (CEFR), followed by an eventual **C1–C2** expansion.

The opportunity is specific: learners need more than a vocabulary habit, but many cannot repeatedly pay for classroom instruction or individual feedback. Canadian immigration provides a strong motivation. IRCC continues to prioritize French-language candidates, and qualifying French proficiency can provide up to 50 additional Express Entry ranking points. These benefits depend on approved test results and broader program eligibility; learning French does not guarantee permanent residence. [1](https://www.canada.ca/en/immigration-refugees-citizenship/campaigns/francophone-immigration-outside-quebec/francophone-immigration-express-entry.html) [1](https://www.canada.ca/en/immigration-refugees-citizenship/news/2026/02/canada-prioritizes-top-talent-in-2026-immigration-express-entry-categories.html)

**Recommended business:** a US$4.99/month, text-first study companion with substantial reusable course content and a transparent AI allowance—not unlimited live voice or guaranteed exam scores. Public API rates suggest text inference can fit this price at thousands of paying users. The larger uncertainties are educational quality, acquisition cost, retention, support, payment access, and production reliability.

**Important implementation findings:** only A1 is currently enabled in the course registry; higher-level source material is present but not an active complete offering. Current TEF/TCF practice is not yet an accurate four-skill Canada-exam simulator. Billing and production usage accounting are not implemented. These are launch requirements, not reasons to abandon the project.

---

## 1. Problem statement

### 1.1 French is a strategic skill for Canadian immigration

Canada is increasing the targeted share of French-speaking permanent residents outside Quebec even while constraining overall immigration volumes. IRCC's May 2026 briefing reports a French-speaking admissions share of **8.9% in 2025**, above its 8.5% target, and targets of **9% in 2026, 9.5% in 2027, and 10.5% in 2028**. The 2026 target corresponds to **30,267 admissions outside Quebec**. These percentages are not a proportion of all applicants and must not be applied to Canada's total population. [1](https://www.canada.ca/en/immigration-refugees-citizenship/corporate/transparency/committees/cimm-may-04-2026/francophone-immigration.html)

The Parliamentary Budget Officer describes the 2026–2028 plan's baseline as **380,000 permanent resident admissions annually**, alongside separate one-time transition initiatives. The opportunity is therefore **targeted preference for relevant skills**, not a claim that Canada is accepting ever more immigrants without restriction. [3](https://www.pbo-dpb.ca/en/publications/RP-2526-025-S--demographic-implications-2026-2028-immigration-levels-plan--implications-demographiques-plan-niveaux-immigration-2026-2028)

### 1.2 News and policy evidence

| Date | Development | Implication for Parlez |
| --- | --- | --- |
| 18 February 2026 | IRCC announced its 2026 categories and confirmed continued French-language invitation rounds. [1](https://www.canada.ca/en/immigration-refugees-citizenship/news/2026/02/canada-prioritizes-top-talent-in-2026-immigration-express-entry-categories.html) | There is a current policy rationale for immigration-focused French learning. |
| 20 February 2026 | CIC News reported the new categories and continued prioritization of French proficiency. This is secondary reporting, not the legal authority. [3](https://www.cicnews.com/2026/02/three-new-express-entry-categories-0271729.html) | The topic is visible in the audience's immigration news channels. |
| 4 May 2026 | IRCC published the Francophone admissions results and rising percentage targets above. [1](https://www.canada.ca/en/immigration-refugees-citizenship/corporate/transparency/committees/cimm-may-04-2026/francophone-immigration.html) | Supports a multi-year opportunity, subject to policy changes. |
| August 2026 consultation record | IRCC described French proficiency as a 2026 priority and discussed 2027 selection considerations. Consultations are not enacted rules. [9](https://www.canada.ca/en/immigration-refugees-citizenship/corporate/transparency/consultations/2026-consultations-express-entry-selection.html) | Policy content needs dates, source links, and an assigned maintenance owner. |

Do not market a historical draw's cutoff as a future admission threshold. Invitations depend on ranking, eligibility, and the instructions for each round.

### 1.3 How many people apply for Canadian PR each year?

There is no single interchangeable number for applicants, profiles, invitations, and admissions. The defensible figures verified for this document are:

| Measure | 2022 | 2023 | 2024 | Average and interpretation |
| --- | ---: | ---: | ---: | --- |
| Express Entry profiles submitted | 428,391 | 488,571 | 468,073 | **About 461,678/year**, 2022–2024. Expressions of interest; not completed PR applications or necessarily unique people. |
| Express Entry PR applications, principal applicants | 34,976 | 80,470 | 85,120 | **About 66,855/year**, 2022–2024; **82,795/year** for 2023–2024. Excludes accompanying family members and non-Express Entry pathways. |
| All-pathway permanent resident admissions | Not used in this calculation | 471,808 | 483,640 | **477,724/year**, 2023–2024. People who became permanent residents, including family members—not people applying that year. |

Sources: IRCC's 2024 Express Entry year-end report, especially Figure 3 and the principal-applicant discussion/Table 23; IRCC's 2025 annual report and PDF. The Express Entry narrative reports 34,976 for 2022 while a destination table rounds to 34,975; the three-year average is deliberately rounded. [1](https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/express-entry-year-end-report-2024.html) [2](https://www.canada.ca/content/dam/ircc/documents/pdf/english/corporate/publications-manuals/express-entry-year-end-report-2024.pdf) [2](https://www.canada.ca/content/dam/ircc/documents/pdf/english/corporate/publications-manuals/annual-report-parliament-immigration-2025.pdf)

**Recommended public wording:** “Canada received roughly 83,000 Express Entry principal-applicant PR applications annually in 2023–2024, while about 478,000 people became permanent residents annually across all pathways.” Do not describe either figure as the annual total of all Canadian PR applicants. An all-pathway, consistently defined annual application series was not verified in this research and should remain an explicit data gap.

These are historical indicators, not a 2026 forecast. The latest complete Express Entry annual report located for this research covers 2024; do not combine partial 2026 draw totals with full-year application counts.

### 1.4 Benefits of French for a PR candidate

1. **Additional CRS points.** NCLC 7 or higher in all four French abilities can earn 25 additional points with English at CLB 4 or lower, or no English test; it can earn 50 with CLB 5 or higher in all four English abilities. Regular first/second-language points are separate and depend on the complete profile. [1](https://www.canada.ca/en/immigration-refugees-citizenship/campaigns/francophone-immigration-outside-quebec/francophone-immigration-express-entry.html) [10](https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/check-score/crs-criteria.html)
2. **French-category eligibility.** NCLC 7 in all four abilities meets the category's language threshold; candidates still need eligibility for an Express Entry-managed program and must satisfy round instructions. [9](https://www.canada.ca/en/immigration-refugees-citizenship/corporate/transparency/consultations/2026-consultations-express-entry-selection.html)
3. **A recognized assessment route.** IRCC accepts **TEF Canada** and **TCF Canada** for French in Express Entry. Results must be less than two years old both at profile completion and PR application submission. [IRCC language-test guidance](https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/documents/language-test.html)
4. **Practical communication.** Beyond points, the product aims to build the language needed for work, services, and participation in French-speaking communities. No employment or salary improvement is promised.

**CEFR is not NCLC.** A1–C2 is a curriculum framework; NCLC is the Canadian French proficiency benchmark. Completing a B2 course, receiving an app badge, or scoring 80% on a practice quiz does not establish NCLC 7. Approved test scores must be converted separately for each ability using current IRCC guidance.

### 1.5 Cost and accessibility of instruction

The founder reports paying **14,000–15,000 every six weeks** for French classes. This document assumes **Nepalese rupees (NPR)** from the Kathmandu context; the currency and included charges should be confirmed before external publication. It is a personal experience, not a statement about every Alliance Française centre.

Alliance Française de Katmandou's published fee table provides a useful local comparison: **NPR 11,900 for a six-week, 45-hour regular session**, with books listed separately at **NPR 2,300 for A1/A2** and **NPR 2,600 for B1/B2**. A session plus a newly purchased book therefore totals **NPR 14,200–14,500** for those levels. Books may be reused across sessions; this is not necessarily the recurring six-week cost. [1](https://www.alliancefrancaise.org.np/french-classes/)

Classroom teaching provides live interaction, accountability, and expert correction. Parlez should complement it rather than claim equivalent outcomes at a fraction of the price. The affordability problem is the repeated cost of personalized practice between classes, plus scheduling and travel constraints.

### 1.6 Why another language app?

The claim should **not** be “Duolingo does not help people learn French.” Duolingo documents CEFR-oriented content through B2 tasks and AI conversation features. General-purpose apps are credible competitors. [2](https://blog.duolingo.com/duolingo-updates/)

The proposed differentiation is narrower: **a continuous path from foundational learning to Canada-specific, four-skill practice**, with explicit task formats, error explanations, writing revision, and skill-by-skill progress. General French practice is useful, but it is not the same deliverable as a validated TEF Canada/TCF Canada preparation system.

---

## 2. Product vision and audience

### Positioning

**“Your affordable French study companion: learn systematically, ask questions naturally, and practise toward your exam goals.”**

The first audience is English-supported beginner and intermediate learners in Nepal and comparable price-sensitive markets, including prospective Canadian immigrants. A second audience is temporary residents in Canada who want to improve French while working or studying. Classroom learners needing extra practice and independent exam candidates are additional segments.

These segments are hypotheses, not validated market shares. Conduct 20–30 interviews and a paid pilot before projecting a total addressable market from immigration statistics. Many PR applicants already speak French, have no French-learning goal, or cannot be reached economically.

### Learning experience

A proposed study session:

1. Choose a level, goal, and available study time.
2. Open a structured lesson with vocabulary, grammar, dialogue, and objectives.
3. Ask the tutor a question without leaving the lesson.
4. Complete targeted exercises and receive immediate feedback.
5. Save difficult vocabulary to spaced-repetition flashcards.
6. Write or speak a short response, revise it, and revisit recurring errors.
7. At the appropriate stage, practise a specific exam task under timed conditions.

A familiar chat layout reduces navigation friction, but chat is the interface—not the curriculum. Every lesson should have a measurable “can do” outcome and a suggested next step.

---

## 3. Scope: current application versus planned product

Repository reviewed: `sazaan/parlez`, working tree on `arena/01a10baa-parlez`, 5 October 2026. Findings below supersede broader claims in the older README.

| Capability | Observed implementation | Required improvement |
| --- | --- | --- |
| Accounts and conversations | Signup/login, JWT authentication, persistent conversation history | Password recovery, verification, account deletion, session management and abuse controls |
| Chat tutor | Lesson/scenario context, level-sensitive prompts, recent history, adaptive prompt additions | Provider abstraction, streaming, quality evaluation, reliable usage metering |
| Course modules | Active registry contains **A1 only: 8 units, 24 lessons** | Review, restructure, and enable A2–B2; validate all levels against learning outcomes |
| Higher levels | A2/B1/B2 files and C1 material exist; inactive in public registry | C1 expansion after core validation; C2 requires new curriculum |
| Exercises | Multiple-choice, fill-blank, translation, conjugation, matching, dictation and other formats | Audit accepted answers, ambiguity, error feedback and item difficulty |
| Flashcards | SM-2-style scheduling, due cards, ratings and statistics | Validate scheduling UX; better leech/difficult-card handling |
| Adaptive practice | Rule-based weak-exercise-type detection and trend analysis | Not a trained learner model; add reliable skill/grammar tagging and mastery evidence |
| Writing feedback | Model-generated correction with parsing and display | Rubric validation, structured-output enforcement, uncertainty and appeals/reporting |
| TEF/TCF practice | Static question banks, timed-practice metadata, grading, history | Correct Canada formats, add productive-skill tasks, validate audio and score claims |
| Voice | Browser speech recognition for dictation; browser speech synthesis and server TTS | Not an oral examiner or pronunciation assessment; replace unsupported TTS dependency |
| Content ingestion | Pasted-text vocabulary extraction, flashcard/quiz generation using local heuristics | Not a general document RAG pipeline; improve vocabulary coverage and review quality |
| Progress and sharing | XP, streaks, results, comments, shared conversation snapshots, export endpoints | Privacy controls, retention, anti-gaming and deletion propagation |
| Subscription | No payment/entitlement system observed | Checkout, billing webhooks, plan limits, cancellation and refund workflows |

**Non-goals at launch:** immigration advice, official certification, guaranteed NCLC/CEFR scores, unlimited human tutoring, unrestricted video/media processing, and fully validated C2 instruction.

---

## 4. Curriculum and exam integrity

The Council of Europe's CEFR distinguishes basic users (A1/A2), independent users (B1/B2), and proficient users (C1/C2). It is a framework of abilities, not merely six labels to attach to lesson collections. [1](https://rm.coe.int/common-european-framework-of-reference-for-languages-learning-teaching/16809ea0d4)

| Stage | Proposed curriculum emphasis | Release gate |
| --- | --- | --- |
| A1 | Introductions, everyday needs, core sounds, simple questions and sentences | Teacher-reviewed lessons and beginner usability pilot |
| A2 | Routine transactions, descriptions, past events, short messages | Four-skill tasks and spaced cumulative review |
| B1 | Connected narration, practical opinions, familiar discussions | Unseen comprehension and supported writing/speaking assessments |
| B2 | Arguments, formal correspondence, inference, sustained interaction | Independent rubric review and exam-task calibration |
| C1–C2 | Nuance, synthesis, register, complex discourse and precise expression | Separate advanced content program and qualified reviewers |

No fixed “zero to B2 in six weeks” promise should be made. Progress depends on prior knowledge, study intensity, feedback, and opportunities for interaction.

### Canada-specific formats to implement

| Skill | TEF Canada | TCF Canada |
| --- | --- | --- |
| Reading | 40 questions; 60 minutes | 39 questions; 60 minutes |
| Listening | 40 questions; 40 minutes | 39 questions; 35 minutes |
| Writing | 2 sections; 60 minutes | 3 tasks; 60 minutes |
| Speaking | 2 sections; 15 minutes | 3 tasks; 12 minutes, including preparation |

Sources: official TEF provider and France Éducation international. These are the immigration versions, not generic TEF/TCF variants. [2](https://www.lefrancaisdesaffaires.fr/en/candidate/test-evaluation-francais/tef-canada/examination/) [TCF Canada official format](https://www.france-education-international.fr/test/tcf-canada?langue=en)

**Current gap:** `mock_tests/data.py` describes TEF reading/listening as 50/60 questions and includes a vocabulary/grammar section. Its TCF metadata uses 29 listening questions, 18 language-structure questions and 29 reading questions—different from TCF Canada. Neither listed exam format includes the complete Canada writing/speaking sequence.

`main.py` also converts raw percentages into level labels using simple thresholds. This is a practice heuristic, **not a validated CEFR assessment or official score conversion**. Replace public readiness claims with skill-specific practice feedback until independent validation exists.

**Content policy:** use original or properly licensed questions, passages, images and recordings. Do not reproduce textbooks, leaked exams, or paid preparation banks without permission. Maintain a rights/provenance register and human approval history. Describe Parlez as independent and unaffiliated with IRCC, Alliance Française, the Council of Europe, and the test owners unless formal agreements exist.

---

## 5. Competitive position

| Alternative | Strength | Opportunity for Parlez | Parlez's disadvantage |
| --- | --- | --- | --- |
| Alliance Française / teachers | Human interaction, accountability and feedback | Affordable between-class practice | AI cannot reliably replace an expert teacher |
| Duolingo / general learning apps | Habit building and broad language practice; Duolingo documents advanced tasks and AI conversation [2](https://blog.duolingo.com/duolingo-updates/) | Explicit Canada-exam workflow and error-to-lesson connections | Larger competitors have established distribution and content teams |
| General AI chat | Flexible explanations and conversation | Curated progression, persistent study goals and reviewed practice | A generic chatbot is easy to imitate; users can prompt alternatives themselves |
| Official exam resources | Authoritative format information and examples [2](https://www.lefrancaisdesaffaires.fr/en/candidate/test-evaluation-francais/tef-canada/examination/) [TCF resources](https://www.france-education-international.fr/test/tcf-canada?langue=en) | Daily structured progression and revision workflow | Parlez has no official assessment authority |
| Specialist preparation providers | Direct exam focus; evaluate individual providers during customer research | Transparent low price and a foundation-to-exam journey | Specialist competitors may have stronger banks and examiner feedback |

**Defensible advantage to build:** reviewed content, reliable feedback, useful longitudinal learning data, and trusted learner outcomes. Low token prices and a chat screen alone are not a durable advantage.

---

## 6. Technical architecture

### Current stack

| Layer | Technology and repository location |
| --- | --- |
| Runtime | Python; Docker and CI target Python 3.12 |
| Web/API | FastAPI 0.104.1, Uvicorn 0.24.0, Pydantic request models; `main.py` |
| Frontend | Vanilla JavaScript, HTML and CSS; `static/app.js`, `index.html`, `styles.css`, separate landing files; no React/Next.js build required |
| Persistence | SQLAlchemy 2.0.25; default SQLite database `data/parlez.db`, WAL mode; `db.py` |
| Data shape | Users plus JSON learning state; shared links and comment groups in separate tables |
| Authentication | bcrypt password hashes, PyJWT HS256 tokens, cookie or bearer authentication |
| AI transport | HTTPX to NVIDIA's chat-completions endpoint; model configured in code as `nvidia/nemotron-3-nano-30b-a3b` |
| Learning engine | Python prompt construction, answer checking, quizzes, adaptive rules, flashcards and writing helpers in `engine/` |
| Course/test content | Python dataclasses and in-repository data in `courses/` and `mock_tests/` |
| Rate limiting | SlowAPI; optional Redis via `REDIS_URL`, otherwise process-local counters |
| Speech | Browser Web Speech APIs; `/api/tts` calls Google Translate's `translate_tts` endpoint—not a contracted Google Cloud TTS integration |
| Operations | Docker Compose, Caddy production proxy, `/health`, request logging, SQLite backup script and backup sidecar configuration |
| Tests and CI | pytest, Ruff, GitHub Actions; configured Bandit, dependency audit, coverage and secret scanning |

Other pinned dependencies include PyPDF2, PyMuPDF, Pillow, aiofiles and scikit-learn. Their presence does not prove that the current app exposes the old README's image/video/PDF upload workflow.

### Request flow

```text
Browser: chat / lesson / exercise / flashcard
                    |
          FastAPI + authentication
                    |
       +------------+------------------+
       |                               |
Local course/practice engine     Tutor prompt builder
       |                         + recent conversation
       |                         + lesson + weak areas
       |                               |
       |                         Hosted model API
       +---------------+---------------+
                       |
             SQLAlchemy / SQLite
                       |
             response + saved progress
```

Chat currently sends up to the last 15 conversation messages plus the system prompt, lesson context and current message. Responses are returned after the upstream call completes rather than streamed token-by-token. Long histories still increase recurring input costs.

### Repository map

- `main.py`: API routes, middleware, orchestration, auth, progress and AI integration.
- `db.py`: persistence interface and SQLAlchemy models.
- `engine/`: reusable educational logic.
- `courses/data.py`: active course registry; the key place to verify actual course availability.
- `mock_tests/data.py`, `expanded_data.py`: practice formats and question banks.
- `static/`: browser UI and public landing page.
- `tests/`: API, security, course, landing, rate-limit and startup regression coverage.
- `backup.py`, `migrate_to_sqlite.py`: data administration helpers.
- `Dockerfile`, Compose files, `Caddyfile`, shell scripts: deployment.

### API groups

Accounts: `/api/auth/*`; courses: `/api/courses/*`; tutor: `/api/chat` and `/api/conversations/*`; exercises: `/api/check-exercise` and `/api/practice/*`; flashcards: `/api/flashcards/*`; exams: `/api/mock-tests/*` and `/api/exam/*`; feedback: `/api/writing/correct`, `/api/adaptive/analysis`; content: `/api/content/ingest`; progress: `/api/progress`, `/api/streaks`; sharing/export: `/api/share/*`, `/api/comments/*`, `/api/export`; audio: `/api/tts`. FastAPI also supplies interactive API documentation at `/docs`.

---

## 7. AI model strategy: can it serve thousands of users?

**Yes, in principle, with paid production APIs, a constrained workload, approved quotas and measured quality.** User count alone does not determine cost or capacity. Active users, turns, context length, output length, peak concurrency, audio and retries do.

### Candidate shortlist

Rates below are published **USD per one million text tokens**, input/output, standard online inference—not consumer chatbot subscriptions or free-tier assumptions. Prices are a research snapshot, not a commercial quote. Qualitative fit is a recommendation to test, not a French-teaching benchmark result.

| Candidate | Input / output | Proposed role | Pros | Cons / validation needed |
| --- | ---: | --- | --- | --- |
| Gemini 2.5 Flash-Lite | $0.10 / $0.40 [1](https://ai.google.dev/gemini-api/docs/pricing) | Low-cost routine tutor candidate | Very low published text cost | Lifecycle/deprecation checks; grammar and feedback quality must be tested |
| Mistral Small 4 (`mistral-small-2603`) | $0.15 / $0.60 [2](https://docs.mistral.ai/models/model-selection-guide?models=mistral-small-4-0-26-03) | Primary paid-pilot candidate | Low price; published Apache 2.0 weights offer deployment flexibility | “Small” is not a hardware sizing guarantee; French accuracy and production quotas need measurement |
| Gemini 3.1 Flash-Lite | $0.25 / $1.50 [1](https://ai.google.dev/gemini-api/docs/pricing) | Alternative primary/fallback candidate | Another economical API route | Output/thinking costs higher than the older Lite model; paid-tier privacy terms need review |
| GPT-4.1 mini | $0.40 / $1.60 [OpenAI model card](https://developers.openai.com/api/docs/models/gpt-4.1-mini) | Writing-review / difficult-answer comparison candidate | Structured outputs, snapshot versioning and no reasoning step documented | Higher cost than the cheapest routes; no direct audio support; not an official examiner |
| Claude Haiku 4.5 | $1.00 / $5.00 [1](https://www.anthropic.com/claude/haiku) | Additional quality benchmark or selective review | Alternative vendor; useful evaluation candidate | More expensive for frequent tutoring at a $4.99 retail price |
| Current NVIDIA Build/NIM route | No production per-token quote verified | Development baseline | Already integrated in the repo | Developer access is for prototyping/testing; production path, licensing and capacity must be confirmed [2](https://docs.api.nvidia.com/nim/docs/product) |

This is a targeted shortlist, not an exhaustive ranking of every model available. Include newly available successors in the evaluation rather than selecting solely by launch date or price.

### NVIDIA-specific commercial caution

NVIDIA's documentation distinguishes Developer Program access from production use and quotes AI Enterprise starting at **$4,500/GPU/year**, or approximately **$1/GPU/hour in the cloud**. Infrastructure and deployment terms still matter. This is not a token price for the currently configured endpoint. [2](https://docs.api.nvidia.com/nim/docs/product)

NVIDIA also describes production partner endpoints as an option. Do not assume a free developer key provides the rights, support, throughput or availability required for a paid consumer app. Do not build a business plan around a universal “40 requests/minute” limit without account-specific confirmation. [5](https://forums.developer.nvidia.com/t/nvidia-nim-faq/300317)

### Recommended routing

- Serve existing lessons, explanations approved for reuse, quizzes and flashcard scheduling **without an LLM call**.
- Trial Mistral Small 4 and Gemini Flash-Lite candidates for ordinary tutoring.
- Use a separately benchmarked model selectively for difficult corrections; higher price does not automatically mean better French teaching.
- Prefer structured outputs for feedback; validate schema and refuse malformed grading payloads.
- Ground explanations in reviewed lesson material, not unrestricted web search on every turn.
- Keep provider/model/version configurable. Add bounded retries, jitter, timeouts, circuit breakers, concurrency limits and cost ceilings.
- Use paid tiers with reviewed data-processing terms. Google lists different product-improvement treatment for free and paid usage; verify the applicable service terms rather than assuming all free APIs protect learner data identically. [1](https://ai.google.dev/gemini-api/docs/pricing)

### Evaluation before choosing a winner

Build at least 200 teacher-reviewed cases across A1–B2: grammatical corrections, acceptable alternative answers, explanations at the requested level, code-switching, writing task fulfillment, ambiguous exercises, and prompt-injection attempts. Use two qualified reviewers for a subset, resolve disagreements, and score blindly.

Track correction precision, incorrect-correction rate, level appropriateness, actionable feedback, schema validity, p50/p95 latency, tokens per turn and cost. Set release thresholds before running the comparison. No live provider benchmark or comparative French assessment was performed for this document.

### API versus self-hosting

Start with managed APIs: low initial expense, no GPU operation, flexible vendor evaluation. Downsides are vendor dependence, rate limits, privacy review and price changes. Self-hosting provides more control but adds GPU rental, idle capacity, patching, scaling, monitoring, failover and staffing.

An illustrative—not quoted—GPU cost of $1/hour is approximately $730/month at 730 hours, before redundancy and operations. Compare against the complete measured API bill and required throughput. “Open weights” does not mean free inference or that one GPU can serve the target concurrency.

---

## 8. Proposed pricing and unit economics

### Offer design

| Plan | Proposed price | Scope |
| --- | --- | --- |
| Starter | Free | Selected beginner lessons and a small lifetime AI trial, e.g. 20 turns per verified account; abuse-limited |
| Parlez Core | **US$4.99/month** | All released core lessons, reusable practice and flashcards; **300 standard AI turns/month**, including up to 20 longer writing reviews within that allowance |
| Annual option | Consider only after retention is measured | Avoid deep launch discounts until support, refunds and model costs are understood |
| Optional extras | Price after measurement | Live voice, unusually long writing, teacher review or additional AI credits; not silently subsidized by Core |

Display remaining allowance before use. Define maximum input/output sizes; long tasks may consume more credits, disclosed beforehand. Do not market unreleased A2–B2 content as available. “All released lessons” does not mean unlimited storage, automation, API access, or unlimited AI generation.

### Text inference calculation

**Planning workload, not a measurement:** 300 monthly AI turns per paying user; 2,500 billed input tokens and 500 billed output tokens per turn, including prompt/history. No caching or batch discounts assumed. Thinking tokens, where billed, must fit the output budget or be added separately.

```text
Monthly input  = 300 × 2,500 = 750,000 tokens
Monthly output = 300 ×   500 = 150,000 tokens
Cost = 0.75 × input price per million + 0.15 × output price per million
```

| All turns on one candidate | Text inference/user/month |
| --- | ---: |
| Gemini 2.5 Flash-Lite | $0.135 |
| Mistral Small 4 | $0.203 |
| Gemini 3.1 Flash-Lite | $0.413 |
| GPT-4.1 mini | $0.540 |
| Claude Haiku 4.5 | $1.500 |

Calculated from the cited rates in Section 7; excludes infrastructure, audio, payments and staff.

**Illustrative blended route:** 90% Mistral Small 4 + 10% GPT-4.1 mini, assuming the same token volumes for both: **$0.236/user/month**; add a 20% inference contingency → **$0.284**. The 10% review share is an assumption, not a demonstrated optimal allocation.

### Sensitivity: where the plan can fail

| Scenario | Blended inference including 20% contingency |
| --- | ---: |
| 100 turns, normal context | $0.095/user/month |
| 300 turns, normal context | $0.284 |
| 900 turns, normal context | $0.851 |
| 3,000 turns, normal context | $2.835 |
| 300 turns, 10,000 input + 1,000 output tokens each | $0.882 |
| Every turn uses Haiku at the normal 300-turn workload | $1.800 |

The repo's current cap is **100 LLM requests/day**, potentially 3,000/month—not the proposed 300-turn subscription allowance. It counts requests rather than billed tokens, and read/modify/write persistence is not an atomic spending control. Implement token metering and reserved budget before exposing paid capacity.

### Illustrative operating contribution

Assumptions: all subscribers pay monthly; every subscriber consumes the standard allocation; payment allowance **$0.50/charge**; refunds/support provision **$0.20/user**; inference as above. Payment allowance is a planning estimate, not a Stripe or Nepal merchant quote. Infrastructure allowances are not vendor quotes or tested sizing.

| Monthly item | 1,000 paying users | 10,000 paying users |
| --- | ---: | ---: |
| Gross subscription receipts | $4,990 | $49,900 |
| Payment processing allowance | −$500 | −$5,000 |
| AI inference + contingency | −$284 | −$2,835 |
| App/database/cache/monitoring allowance | −$200 | −$1,000 |
| Refund/support provision | −$200 | −$2,000 |
| **Contribution before excluded costs** | **$3,806** | **$39,065** |
| Contribution / gross receipts | 76.3% | 78.3% |

**Not net profit.** Excludes founder/employee pay, teacher review, acquisition, free users, legal/accounting, tax, payment FX/cross-border surcharges, chargebacks beyond the provision and uncapped audio. At only 100 paid users, the same $200 infrastructure allowance would consume $2 per subscriber.

Using the 1,000-user case, contribution is about $3.81 per paid user after the shown allocations. An additional $3,000/month in fixed payroll/content overhead would require roughly **789 equivalent subscribers** at that contribution; $10,000 would require roughly **2,628**. This is a simplified sensitivity, not a cash-flow forecast, and must be recalculated as infrastructure and staffing change.

### Voice, payments and affordability

OpenAI lists `gpt-4o-mini-transcribe` at an estimated **$0.003/minute**; 60 minutes is $0.18 for transcription alone. Synthesis and tutoring are extra. Its listed GPT-Live session rate of **$0.05/minute** would be $3 for 60 minutes before separately billed backend usage. This illustrates why unlimited live voice should not be included at $4.99. [OpenAI audio pricing](https://developers.openai.com/api/docs/pricing)

Reuse licensed/pre-generated lesson audio; use browser synthesis where suitable but disclose voice/browser variation. Replace the current Translate endpoint with a supported commercial speech service before relying on server speech at scale.

For a Nepal-based business, verify merchant eligibility, settlement currency, recurring-payment support, tax collection and customer card access **before** selecting a gateway. Compare a local gateway, eligible international processor, or merchant-of-record arrangement using written terms. Do not assume US merchant fees or that availability to buyers means availability to Nepal-based sellers.

At $4.99 monthly, twelve payments total $59.88 before tax. Do not claim a precise percentage saving versus local instruction without a dated exchange rate and a like-for-like comparison; self-study and 45 hours of teacher-led learning are different products.

---

## 9. Scaling plan and operational risks

### Capacity example

At 10,000 paid users × 300 turns/month, the app handles **3 million AI requests/month**. Over a 30-day month this averages **69.4 requests/minute**. A planning peak of 10× average is approximately **694 requests/minute**, **1.74 million input tokens/minute**, and **347,000 output tokens/minute** at the assumed payload.

At a 10-second average upstream response time, the peak would imply roughly **116 simultaneous AI requests**. These are assumptions for quota discussions and load tests—not observed performance. Check requests, tokens, daily quotas, burst rules and concurrency independently; include fallback capacity and retries.

### Architecture progression

**Pilot:** one app replica, SQLite, strict concurrency controls, verified backups and measured API costs. A single process can still have overlapping asynchronous requests; it does not remove lost-update risk.

**Paid growth:** managed PostgreSQL, normalized conversation/message/review/usage tables, transactional updates, shared Redis limits, reusable HTTP clients, bounded background jobs, monitoring and documented restore procedures.

**Thousands of active learners:** horizontally scaled stateless API services behind a trusted proxy, connection pooling, durable queues, object storage/CDN for reviewed audio, centralized billing/usage ledger, quota headroom and failover tests.

PostgreSQL is **not** a drop-in scaling guarantee. Although `db.py` accepts a database URL, the current requirements do not include a PostgreSQL driver, and whole-user JSON updates can overwrite concurrent changes on any database. Add a driver, migrations, transactional/optimistic concurrency controls and tests.

### Launch blockers and mitigations

| Risk | Why it matters | Action |
| --- | --- | --- |
| Inaccurate instruction or false grading | Can teach errors or mislead exam decisions | Teacher-reviewed evaluation, reporting, correction logs, no official-score claims |
| Misaligned exam formats | Undermines the core positioning | Canada-specific four-skill implementation and expert sign-off |
| Curriculum/IP uncertainty | Textbook conversion utilities and legacy materials warrant provenance review | Audit source rights; replace unlicensed content |
| Provider terms / outage | Free developer access is not a production contract | Paid provider approval, fallback, budgets and graceful offline practice |
| Concurrent JSON saves | Can lose history, XP or quota updates | Normalize records and use atomic writes before multi-replica deployment |
| Payment and subscription abuse | $4.99 leaves limited room for fraud/support | Signed idempotent webhooks, server-side entitlements, trial abuse limits |
| Proxy/security configuration | App trusts forwarded IPs; direct access can undermine rate limits | Restrict backend ingress and trust only known proxies; review auth and dependency advisories |
| Privacy | Conversations may contain personal or immigration-related information | Minimize collection; no passport uploads; consent, retention, deletion and vendor disclosures |
| Backup reliability | A separate volume is not necessarily an off-site backup | Verify sidecar permissions/read-only WAL behavior, restore drills, encrypted off-host copies |
| Policy changes | Could weaken acquisition messaging | Date policy guidance; quarterly review; retain broader language-learning value |

The production Compose file currently exposes port 8000 as well as Caddy. Remove direct public backend exposure when deploying behind the proxy. The backup sidecar mounts app data read-only while `backup.py` constructs the storage layer; verify startup and restore behavior rather than assuming the configured sidecar is proven. No security certification, full compliance review or production load test is claimed.

---

## 10. Development and deployment guide

### Local Docker setup

Prerequisites: current Docker Engine/Compose, an NVIDIA key for the current prototype route, and an independently generated JWT secret.

```bash
cp .env.example .env
openssl rand -hex 32
# Edit .env: set NVIDIA_API_KEY and JWT_SECRET to your own values.
# Keep COOKIE_SECURE=false only for local HTTP development.
./run.sh
```

Open `http://localhost:8000`; the public landing page is `/`, with the login/application entry at `/login`. For health and logs:

```bash
docker compose logs --tail=100 chatbot data-init
curl http://localhost:8000/health
```

The working tree's Compose configuration includes a one-shot root `data-init` service that repairs ownership of the `./data` bind mount, followed by the non-root app. Initializer exit code 0 is expected. Preserve `data/parlez.db`; do not delete it to repair permissions. An explicit SQLite URL inside Docker should use the container path: `sqlite:////app/data/parlez.db`.

### Manual development

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
# Configure .env as above, then:
python main.py
```

Run tests against the isolated test database configured by `tests/conftest.py`:

```bash
JWT_SECRET=this-is-a-test-secret-that-is-32-chars-long \
NVIDIA_API_KEY=dummy python -m pytest tests/ -q
ruff check main.py db.py engine migrate_to_sqlite.py
```

These are operating instructions, not a claim that the full suite was executed while preparing this document. Never use real user data for testing.

### Configuration checklist

- `NVIDIA_API_KEY`: current upstream credential; keep server-side.
- `JWT_SECRET`: required, at least 32 characters; generate securely, never commit.
- `TOKEN_EXPIRY_HOURS`: token lifetime, default 24.
- `COOKIE_SECURE`: false only for local HTTP; true for production HTTPS.
- `COOKIE_SAMESITE`: default `lax`; review alongside CSRF protections.
- `DATABASE_URL`: optional; default SQLite storage.
- `REDIS_URL`: optional shared rate-limit store; no Redis service is automatically provisioned by this setting.
- `PARLEZ_HOST`: Caddy host setting for the production Compose configuration.

Before production: review secrets, domain/TLS, trusted proxy settings, data ownership, backup restores, rate limits, upstream production rights, privacy notices and payment eligibility. Separate deployment readiness from educational readiness.

---

## 11. Delivery roadmap and success measures

Indicative phases assume engineering capacity plus a qualified French curriculum reviewer; they are planning ranges, not delivery commitments.

| Phase | Indicative duration | Acceptance criteria |
| --- | --- | --- |
| Foundation audit | 2–3 weeks | Content inventory, IP review, A1 accuracy review, corrected exam labels, basic observability |
| Learning beta | 4–8 additional weeks | A1/A2 reviewed, model comparison completed, 30–50 consented pilot learners, metered costs |
| Paid Core readiness | 6–10 additional weeks | Billing and cancellation tested, privacy/security review, reliable backups, approved API quotas |
| B1/B2 and Canada preparation | Separate content-led workstream | Reviewed four-skill lessons, exact task formats, unseen assessments, qualified reviewer sign-off |
| C1/C2 expansion | After core outcomes and retention are demonstrated | Dedicated advanced curriculum, specialist review and sustainable economics |

### Metrics

- **Activation:** account → first lesson → first completed practice session.
- **Learning:** unseen-question performance, recurring-error reduction, rubric-based writing/speaking improvement; not just XP.
- **Retention:** day 7/day 30 and paid cohort retention, study days per week, voluntary churn reasons.
- **Economics:** paid conversion, net revenue, AI cost at median/p95, support minutes, refunds, acquisition cost and payback.
- **Reliability:** tutor error rate, p95 latency, malformed feedback, quota failures and restore success.
- **Evidence:** optional, consent-based before/after official scores; report sample size and selection bias. Never imply the app alone caused immigration success.

For initial planning, target AI cost below $0.75 for a typical Core subscriber and below $1.50 for most subscribers within the promised allowance. These are proposed guardrails, not achieved metrics. Evaluate acquisition payback against measured contribution; a three-month payback budget at approximately $3.81 contribution is only about $11.43 per acquired paid user.

### Go-to-market

Start with the founder's learner community and a transparent paid pilot. Publish source-linked explanations of exam formats and learning strategies; build referral loops around useful free exercises, not immigration guarantees. Explore teacher partnerships for supplemental practice. Add Nepal-friendly payment options only after merchant and settlement validation. Avoid expensive paid acquisition until retention and conversion are known.

---

## 12. Recommendation and decisions required

**Proceed with a focused, text-first pilot—not an “unlimited AI immigration coach.”** A $4.99 subscription is plausible on inference economics, but product-market fit and validated learning outcomes remain unproven.

Priorities:

1. Confirm USD pricing and the currency/details of the founder's fee example.
2. Audit course accuracy and content rights; publish only reviewed levels.
3. Correct TEF Canada/TCF Canada positioning and build all four skills.
4. Benchmark paid production models, then choose on educational quality and measured cost.
5. Implement transactional usage metering, billing, privacy controls and restore-tested storage.
6. Run a small paid cohort and decide whether to expand from evidence.

**Product summary:** Parlez is an affordable French study companion connecting a structured curriculum, conversational explanations, repeated practice and progress feedback. Its long-term ambition is A1–C2 learning; its near-term promise should be a credible, reviewed foundation and a progressively validated path toward Canada-specific exam preparation.

---

## Research notes and source register

Inline links identify the evidence behind external claims. Primary government, exam-owner and provider documentation is preferred; third-party news is explicitly identified. All sources were consulted for this document on **5 October 2026**. Rates and public pages may change. Numerical projections are calculations from stated assumptions, not provider performance guarantees.

### Immigration and demand

- IRCC — French-speaking skilled workers and additional points: https://www.canada.ca/en/immigration-refugees-citizenship/campaigns/francophone-immigration-outside-quebec/francophone-immigration-express-entry.html
- IRCC — current CRS criteria: https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/check-score/crs-criteria.html
- IRCC — February 2026 announcement: https://www.canada.ca/en/immigration-refugees-citizenship/news/2026/02/canada-prioritizes-top-talent-in-2026-immigration-express-entry-categories.html
- IRCC — May 2026 Francophone briefing: https://www.canada.ca/en/immigration-refugees-citizenship/corporate/transparency/committees/cimm-may-04-2026/francophone-immigration.html
- IRCC — Express Entry 2024 report: https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/express-entry-year-end-report-2024.html
- IRCC — 2025 annual report, covering 2024 admissions: https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/annual-report-parliament-immigration-2025.html
- Parliamentary Budget Officer — 2026–2028 plan analysis: https://www.pbo-dpb.ca/en/publications/RP-2526-025-S--demographic-implications-2026-2028-immigration-levels-plan--implications-demographiques-plan-niveaux-immigration-2026-2028
- CIC News — secondary reporting: https://www.cicnews.com/2026/02/three-new-express-entry-categories-0271729.html

### Teaching, tests and alternatives

- Alliance Française de Katmandou fees: https://www.alliancefrancaise.org.np/french-classes/
- Council of Europe CEFR companion volume: https://rm.coe.int/common-european-framework-of-reference-for-languages-learning-teaching/16809ea0d4
- TEF Canada examination: https://www.lefrancaisdesaffaires.fr/en/candidate/test-evaluation-francais/tef-canada/examination/
- TCF Canada: https://www.france-education-international.fr/test/tcf-canada?langue=en
- IRCC accepted language tests and validity: https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/documents/language-test.html
- Duolingo product description: https://blog.duolingo.com/duolingo-updates/

### AI and pricing

- Google Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
- Mistral model comparison: https://docs.mistral.ai/models/model-selection-guide?models=mistral-small-4-0-26-03
- OpenAI GPT-4.1 mini: https://developers.openai.com/api/docs/models/gpt-4.1-mini
- OpenAI audio and service pricing: https://developers.openai.com/api/docs/pricing
- Anthropic Haiku: https://www.anthropic.com/claude/haiku
- NVIDIA NIM product FAQ: https://docs.api.nvidia.com/nim/docs/product
- NVIDIA developer/production FAQ: https://forums.developer.nvidia.com/t/nvidia-nim-faq/300317

### Evidence still required

An all-pathway annual PR application series; primary customer interviews; willingness to pay; content ownership clearance; teacher-reviewed learning and model benchmarks; actual token distributions; provider quotas and commercial terms; payment settlement eligibility; production load and restore tests; and a legal/privacy review. No speculative market size, PR approval rate, or AI teaching accuracy is presented as an established fact.
