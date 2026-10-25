# French curriculum: source register and redesign blueprint

- **Implementation status:** The mission-led A2–B2 draft content is integrated in the app; A1 has course and module outcome/capstone metadata. TEF Canada and TCF Canada now have distinct format references and original writing/speaking practice tasks, alongside shorter reading/listening practice sets. None of this content is independently educator-reviewed or certified.
- **Research checked:** 25 October 2026.
- **Scope:** Adult general French from A1 to B2, with a separate, optional TEF Canada / TCF Canada preparation pathway.
- **Publication rule:** A1 remains the only level enabled by default. A2–B2 remain unpublished by default and require qualified review before release.

This document records a vetted starting set of curriculum references, open materials, and external practice resources, then proposes a task-led course spine. It deliberately distinguishes **authoritative references**, **materials with reuse permissions**, and **free-to-access materials that Parlez must not copy without permission**. It is a design brief, not a claim that existing modules are CEFR-validated or that a learner's progress predicts an official exam result.

## 1. Executive decisions

1. Use the **CEFR Companion Volume (2020)** as the general outcomes framework. Organize learning around purposeful tasks and observable outcomes, including reception, production, interaction and mediation—not grammar chapters with a level label.
2. Use **NCLC and the CLIC adult curriculum** as an additional Canadian-adult-learning lens. Keep NCLC and CEFR distinct; do not invent a level-to-level crosswalk. Use current IRCC tables only when displaying official test-score equivalencies.
3. Keep **general French** and **Canada exam preparation** connected but separate. TEF Canada and TCF Canada have different, version-sensitive task structures. Neither exam path should be a generic “French test” unit.
4. Prefer original Parlez examples, dialogues, audio and tasks. The best identified commercially reusable starting materials are COERLL resources with a verified **CC BY** license; use the exact version and retain attribution. Exclude noncommercial resources from a paid product unless separate permission is obtained.
5. Link to useful external practice rather than importing it. “Free to access” does not mean “licensed to copy, host, adapt, or use for AI generation.”
6. Keep current higher levels unpublished until the curriculum and the assessment evidence meet the release gates in §8.

## 2. Current-course audit

The runtime course catalog is highly uneven in size and is organized mainly around topics or grammar points. Counts below were read from `courses.data.COURSE_CATALOG`; the minutes are the values stored on current lessons, not a CEFR workload estimate or a measure of proficiency.

| Level | Units | Lessons | Stored lesson minutes | Observed shape |
| --- | ---: | ---: | ---: | --- |
| A1 | 8 | 24 | 775 | Thematic sequence: first contacts, identity, family, routine, town, food, home, hobbies/plans |
| A2 | 6 | 7 | 245 | Five one-lesson units and one two-lesson unit; several grammar-led topics |
| B1 | 5 | 6 | 225 | Four one-lesson units and one two-lesson unit |
| B2 | 5 | 6 | 240 | Four one-lesson units and one two-lesson unit |

**Main gaps**

- A1 has useful everyday topics, but its module outcomes are not explicitly mapped to source descriptor scales, interaction strategies, mediation, or a level-end performance profile.
- A2–B2 are too small and uneven to represent a comprehensive course: 19 lessons are spread across 16 units. Several lessons are grammar topics with a dialogue and a small exercise set, rather than a sustained sequence of increasingly independent communicative tasks.
- The data model has lesson objectives, vocabulary, grammar, dialogues and exercises, but no first-class fields for level outcomes, communicative mode/skill evidence, module capstone, performance rubric, cumulative review plan, or content-rights provenance.
- The current formats emphasize closed-answer practice. They do not, by themselves, demonstrate that learners can understand an unfamiliar text/audio, sustain an interaction, or produce a useful spoken or written artifact. Pronunciation/phonology is not mapped as a level-by-level strand.
- There is no course-level rule requiring old language to return in new contexts. Existing flashcard scheduling is useful, but it is not a substitute for a curriculum-wide retrieval and review plan.
- **Historical content-integrity defect in A2–B2:** a recursive audit found 166 A2, 154 B1 and 130 B2 string values (450 total) in the original active drafts ending in a literal backslash, leaving phrases, examples, dialogue lines and exercises incomplete. The runtime A2–B2 files have since been replaced with newly authored draft content; the tracked `.bak` files remain corrupt legacy copies and are not imported or safe restore candidates. A runtime catalog scan now finds no course strings ending in a literal backslash. The active A1 course had no such fields; its legacy copy did.
- B1 retains the legacy unit and lesson ID `I am tired.` to avoid losing existing completion and publication references. It is a known malformed ID, not a learner-facing title. Do not change it without a versioned migration that maps stored progress and unit-publication settings.
- Source and status boundaries can be confusing: `courses/data.py` defines C1 material but omits it from `COURSE_CATALOG`; older/backup course files also remain beside the files imported by the catalog. Confirm all references before consolidating or deleting any of them.
- The application publishes A1 by default. A2–B2 stay inaccessible until a version-bound qualified-educator review attestation is recorded and an administrator explicitly enables them. The attestation is self-reported and does not verify credentials or certify CEFR alignment; verify the reviewer independently. A module title, lesson count, XP, or practice accuracy must not be presented as proof of CEFR mastery.

**Preserve and build on:** existing unit and lesson IDs are retained, including the malformed B1 legacy ID, so learner completion and publication settings are not orphaned. New lessons use new IDs. The old `.bak` data remains only as an untrusted legacy copy; do not restore it. Any future ID cleanup must use a versioned migration.

## 3. Recommended course architecture

### 3.1 A mission-led unit, not a grammar bucket

Each unit should start with a recognizable adult-life mission and end in an artifact or interaction that shows the learner can do something with the language. Teach grammar, vocabulary, pronunciation and pragmatics as resources for that mission.

A unit specification should eventually include:

- **Mission and context:** who is communicating, for what purpose, with whom, and under what constraints.
- **Original outcomes:** short, observable “learner can…” statements written for Parlez. Internally link them to the relevant CEFR descriptor scale/level, but do not copy large blocks of copyrighted descriptor text.
- **Communication coverage:** reception, production, interaction and mediation tags, with the actual evidence a learner must produce or interpret.
- **Language resources:** vocabulary, grammar, sound/spelling and pronunciation, register, politeness, discourse moves and repair strategies—sequenced in response to the task.
- **Input:** a rights-cleared or original short text/audio/video prompt, with transcript/captions and accessible alternatives where appropriate. Record the asset's source and exact reuse terms.
- **Practice and feedback:** controlled practice followed by transfer to a new example; immediate feedback for objectively scored items and criteria-based coaching for open work.
- **Cumulative return:** planned retrieval of prior language in later lessons/units, not just a list of flashcards.
- **Capstone and rubric:** an integrated task plus transparent, skill-specific criteria. Keep Parlez feedback clearly unofficial.
- **Provenance:** author/source, asset-level license, attribution, modifications, review date, reviewer and course version.

### 3.2 A repeatable learning rhythm

A typical unit can use the following pattern; lesson count and duration should be validated with adult learners rather than treated as a fixed CEFR formula.

1. **Set the goal:** preview the mission and do a low-stakes diagnostic attempt.
2. **Understand:** listen/read for gist and then useful details; introduce strategies for inference, clarification and noticing.
3. **Build the language:** teach the grammar, vocabulary, pronunciation and register needed for the task in context.
4. **Rehearse:** use varied, progressively less scaffolded exercises and revisit earlier language.
5. **Act:** perform the mission with a new prompt; save a written, spoken or interaction artifact and give actionable feedback.
6. **Return:** schedule short mixed review after a delay and include the language in later units.

A1 practice can replay audio and provide transcripts. Only a clearly labeled, optional exam simulation should enforce exam-like limits such as a single audio play. Accessibility and learning support take priority outside timed simulations.

### 3.3 Proposed A1–B2 mission map

This eight-unit spine is implemented as an original **draft curriculum** in the app, not copied CEFR wording, a final validated syllabus, or a promise that eight units alone cover a CEFR level. A1's existing 24 lessons are retained and annotated with outcomes and capstones. A2–B2 are at content version 2026.2: each has 24 original lessons (three per unit), corrected existing French/translation examples, revised unit outcomes and capstone criteria, retrieval practice, and an unscored transfer task in each new lesson. Existing unit and lesson IDs are preserved. The expansion improves breadth; it is not qualified French-educator review, a learner pilot, or a CEFR validation. Keep A2–B2 unpublished until those gates are completed, and continue revising where reviewer and learner evidence shows gaps.

#### A1 — handle familiar, immediate situations with simple language

| Unit | Mission | End-of-unit evidence |
| --- | --- | --- |
| 1. First contact | Greet someone, introduce yourself, spell a name, ask for repetition or slower speech. | Short self-introduction and a simple two-way greeting. |
| 2. People and identity | Exchange basic details, describe people and relationships, complete a simple profile. | Profile plus a short exchange asking and answering personal questions. |
| 3. A day in my life | Understand and give simple times, schedules and routine information. | A simple daily schedule explained in a short message or voice note. |
| 4. Around town | Ask where a place is, understand a basic route and make a simple transport choice. | Route plan and a brief directions role-play with a clarification request. |
| 5. Food and everyday purchases | Read a simple menu/list, order politely, ask a price and identify basic quantities. | Complete a café/shop role-play and check the order. |
| 6. Home and neighbourhood | Describe a familiar home, locate items/places and ask a basic question about a listing. | Compare two simple home descriptions and ask for one missing detail. |
| 7. Invitations and near-future plans | Invite, accept/decline politely, agree on a time/place and describe an immediate plan. | Send an invitation and negotiate a simple plan. |
| 8. Integrated A1 mission | Plan a simple day with another person using places, times, food and transport. | Short plan plus a supported conversation; demonstrate at least one repair/clarification strategy. |

**Language progression to plan:** sound–spelling links and intelligibility from the start; names/numbers; articles and agreement; present-tense high-frequency verbs; questions and negation; time/place expressions; polite requests; near-future forms. This is a planning list, not a requirement to front-load grammar terminology.

#### A2 — manage routine exchanges and give short connected accounts

| Unit | Mission | End-of-unit evidence |
| --- | --- | --- |
| 1. Tell what happened | Describe a recent experience and distinguish the main event from background/routine details. | Short oral or written account with a clear sequence. |
| 2. Travel and changes | Arrange a trip, understand practical information and respond to a routine disruption. | Travel plan plus a role-play requesting a change or help. |
| 3. Health and appointments | Describe a common concern, arrange an appointment and understand simple instructions. | Appointment exchange and a concise follow-up note; do not use real medical advice. |
| 4. Housing and local services | Ask about a home/service, describe a problem and make a polite request. | Message/request with the relevant details and a follow-up question. |
| 5. Food, shopping and comparisons | Follow a simple recipe/list, compare choices and handle a basic purchase problem. | Shopping plan and an exchange explaining a preference or simple issue. |
| 6. Work and learning routines | Describe regular tasks, schedules and a familiar problem at work or in study. | Short update/message and a simple request for clarification or help. |
| 7. Social plans and digital messages | Suggest, respond, explain a preference and agree on a shared plan. | A short message thread plus a negotiated plan. |
| 8. Integrated A2 mission | Organize a weekend activity in a Francophone setting and adapt when one detail changes. | Read/listen to practical information, negotiate, produce a plan and report what changed. |

**Language progression to plan:** past narration and background; future plans; comparison/quantity; advice and requests; common object pronouns and connectors where useful; register and repair strategies. Teach forms in service of the mission and revisit them after introduction.

#### B1 — participate independently in familiar public, social and work/study contexts

| Unit | Mission | End-of-unit evidence |
| --- | --- | --- |
| 1. Experiences and stories | Narrate a connected experience and explain its outcome or significance. | Structured story with a clear timeline and relevant detail. |
| 2. Work and study collaboration | Explain a role/task, ask follow-up questions and contribute to a shared plan. | Short planning interaction and a written summary of next steps. |
| 3. Solve a service or consumer problem | Explain a problem, understand options and negotiate a reasonable solution. | Call/message role-play with clarification, explanation and a clear request. |
| 4. News and media | Identify a report's main point and supporting details; distinguish fact from opinion at an introductory level. | Short oral or written summary that identifies the source and main point. |
| 5. Opinions and discussion | State a position, support it with reasons/examples and respond to a different view. | Short presentation or discussion with a follow-up response. |
| 6. Community and environment | Discuss a familiar issue and propose a practical action. | Proposal with reasons, plus questions/feedback from a partner. |
| 7. Francophone perspectives and mediation | Compare perspectives respectfully and explain key information to another person. | Short mediated summary that preserves the source's main meaning. |
| 8. Integrated B1 mission | Develop a proposal for a community, work or study project using more than one input. | Read/listen, summarize, present a proposal, answer questions and record an agreed next step. |

**Language progression to plan:** connected narration, common discourse markers, reported information, giving reasons and examples, expressing uncertainty, interaction management, reformulation and increasing control of formal/informal registers.

#### B2 — handle complex material, nuance, sustained discussion and purposeful formal communication

| Unit | Mission | End-of-unit evidence |
| --- | --- | --- |
| 1. Debate with nuance | Present a position, qualify a claim, concede a point and respond to a counterargument. | Sustained discussion or short argument with a reasoned reply. |
| 2. Compare and synthesize sources | Identify stance/evidence across written and spoken sources and combine the key ideas. | Concise synthesis that distinguishes source claims from the learner's own view. |
| 3. Professional communication | Write to an appropriate audience, explain a complex issue and negotiate next steps. | Formal email/report extract plus a meeting or interview role-play. |
| 4. Media and digital claims | Assess a source's purpose, evidence and uncertainty without assuming every claim is true. | Evidence-based comparison and a cautious summary. |
| 5. Francophone cultures and register | Discuss cultural/language variation without treating Francophone communities as one monolith; adjust register. | Context-sensitive contribution and reflection on audience/register choices. |
| 6. Explain a complex issue | Explain a scientific, social or economic question, including a hypothesis and evidence. | Structured explanation with an appropriate example and qualification. |
| 7. Facilitate and mediate | Help people with different views understand each other and identify a possible resolution. | Mediated summary and a proposed next step that represents both positions fairly. |
| 8. Integrated B2 mission | Develop a recommendation from multiple sources and present it to a decision-making audience. | Written recommendation, oral presentation, questions and a revised conclusion. |

**Language progression to plan:** cohesion and thematic development, register flexibility, hedging/qualification, complex argument, paraphrase/synthesis, inferencing and more precise pronunciation/intonation. Grammar remains a resource strand—not the unit title or the only evidence of progress.

### 3.4 Adult-learner and accessibility choices

- Use adult-relevant domains: personal life, community, services, learning, work and digital communication. Let learners select priorities without implying that a course outcome guarantees employment, citizenship or immigration success.
- Include varied Francophone voices and contexts. Teach regional variation as variation, not as a single “correct” accent; label model voices and transcripts.
- Support low-bandwidth/mobile use: concise activities, downloadable rights-cleared resources where appropriate, transcripts/captions, keyboard operation and a non-audio alternative for essential instructions.
- Do not rate a learner's accent as identity or equate browser speech recognition with pronunciation assessment. Keep pronunciation goals about intelligibility and sound distinctions, and label automated feedback as approximate.

## 4. Separate Canada exam pathway

The general course builds French ability. The exam pathway should then build familiarity with **one selected test variant**, its timing, task instructions and per-skill demands. Store the provider source, test variant, verification date and version with every format definition. Re-check before release; exam owners can change formats.

### Current official formats checked on 25 October 2026

| Skill | TEF Canada (immigration version) | TCF Canada |
| --- | --- | --- |
| Listening | 40 MCQs; 40 minutes | 39 MCQs; 35 minutes |
| Reading | 40 MCQs; 60 minutes | 39 MCQs; 60 minutes |
| Writing | 2 sections in 60 minutes: A, continue an article (minimum 80 words, 25 min); B, express and justify a viewpoint (minimum 200 words, 35 min) | 3 tasks in 60 minutes: message (60–120 words); account/story for several recipients (120–150); compare two views and give an opinion (120–180) |
| Speaking | 2 face-to-face sections in 15 minutes: obtain information (5 min) and persuade (10 min) | 3 tasks in 12 minutes: structured interview (2 min, no prep); interaction (5.5 min, including 2 min prep); express a point of view (4.5 min, no prep) |

Sources: [TEF Canada official examination page](https://www.lefrancaisdesaffaires.fr/en/candidate/test-evaluation-francais/tef-canada/examination/) and [preparation resources](https://www.lefrancaisdesaffaires.fr/en/candidate/test-evaluation-francais/tef-canada/preparation/) (including official [writing](https://www.lefrancaisdesaffaires.fr/wp-content/uploads/2024/10/tef-exemples-epreuve-ee.pdf) and [speaking](https://www.lefrancaisdesaffaires.fr/wp-content/uploads/2024/10/tef-exemples-epreuve-eo.pdf) sample PDFs); [TCF Canada official page](https://www.france-education-international.fr/en/test/tcf-canada) and [how a TCF session is administered](https://www.france-education-international.fr/en/node/199?langue=en). The TCF page says its listening recordings play once and its tasks become progressively harder. These provider examples are for reference through the providers' sites, not content Parlez may copy or embed. Practice should be original; do not copy items into Parlez.

### Implementation guardrails

- Keep two distinct test records and user flows: **TEF Canada** and **TCF Canada**. Do not mix TEF's two writing sections with TCF's three writing tasks, or introduce a generic language-structures section into either Canada variant.
- The app now distinguishes **TEF Canada** from **TCF Canada**, shows provider-linked format references and official section counts/timings, and includes original writing/speaking prompts with self-checks. Listening/reading banks remain short Parlez practice sets; this is not a full-length mock exam. The older generic grammar-question arrays are not part of the Canada pathway.
- Create prompts in Parlez's own words. Match task type and time limits, not secure/live exam content. Label practice as unofficial. A percentage reports accuracy on the selected practice items only; it is not a TEF/TCF score, a CEFR/NCLC estimate, or evidence of exam readiness.
- Teach listening with replay/transcripts during normal learning; provide one-play conditions only in a clearly labeled, optional timed simulation. Do not use TV5MONDE/RFI material as embedded test stimuli without explicit rights.
- Give separate feedback for listening, reading, writing and speaking. A percentage from a small multiple-choice set is not an official CEFR, TEF or TCF score. Open writing/speaking tasks need a transparent unofficial rubric and, before level claims, qualified human review.
- The official [IRCC language-test page](https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/documents/language-test.html) lists accepted tests and NCLC-related rules. Thresholds, programs and equivalencies can change. Link users to IRCC and the exam provider; do not tell users they qualify for immigration based on Parlez progress or offer immigration advice.
- Optional general-purpose credentials such as DELF can inform separate practice, but do not mix their task formats with TEF Canada or TCF Canada.

## 5. Vetted source register

“Authority” below means useful for standards/specifications, not automatically reusable content. The permission notes are a conservative product-content screen, not legal advice. Check the source and exact asset again before using it in a release.

### 5.1 Standards and authoritative references — use to design and check, not copy wholesale

| Source | Best use for Parlez | Rights / implementation note |
| --- | --- | --- |
| [Council of Europe, CEFR Companion Volume (2020)](https://rm.coe.int/common-european-framework-of-reference-for-languages-learning-teaching/16809ea0d4), [descriptor search](https://www.coe.int/en/web/common-european-framework-reference-languages/cefr-descriptors), [action-oriented approach](https://www.coe.int/en/web/common-european-framework-reference-languages/the-action-oriented-approach) | General A1–B2 outcome spine; profiles across skills; reception, production, interaction, mediation, online interaction, plurilingual/pluricultural competence and phonology. | The Companion Volume states “All rights reserved.” Use it as a reference, cite descriptor scale IDs internally, write original Parlez outcomes, and seek permission for substantial reproduction. It is not a blanket OER license. |
| [NCLC: French as a Second Language for Adults](https://www.language.ca/product/pdf-f-001-nclc-francais-langue-seconde-pour-adultes/) | Canadian adult-learning lens across listening, speaking, reading and writing; useful for locating functional needs in Canadian contexts. | The CCLB page says the document remains property of IRCC. Do not republish descriptor text or assume that a free/downloadable PDF is licensed for adaptation. CEFR and NCLC are not interchangeable scales. |
| [National CLIC Curriculum Framework](https://clic.language.ca/wp-content/uploads/2024/07/Cadre-national-du-curriculum-CLIC_Juin-2024.pdf), [CLIC module/lesson guidelines](https://clic.language.ca/lignes-directrices-nationales-du-curriculum-clic/) | Strong adult/newcomer program-design reference: needs analysis, real-life tasks, four skills, grammar in service of communication, Canadian Francophone contexts, EDI, multilingual backgrounds and digital skills. | No general reuse license was identified in the consulted materials. Use as a design reference and link; get permission before adapting its plans, descriptors, examples or worksheets. |
| [IRCC: Express Entry language-test results](https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/documents/language-test.html) | Verify which French tests are currently accepted and where score-to-NCLC conversions are published. | Requirements and thresholds are program- and date-dependent. Link to current IRCC information instead of hard-coding immigration advice in lessons. |
| [OQLF Vitrine linguistique](https://vitrinelinguistique.oqlf.gouv.qc.ca/), including the [BDL](https://bdl.oqlf.gouv.qc.ca/bdl) and [GDT](https://gdt.oqlf.gouv.qc.ca/?lang=fr/) | Check Quebec/Canadian usage, grammar, orthography and specialist terminology; show variation with context and labels. | Individual OQLF data sets may carry specific reuse terms; do not scrape/copy the site as a whole. Check the exact record and [Vitrine FAQ](https://vitrinelinguistique.oqlf.gouv.qc.ca/a-propos-de-la-vitrine-linguistique/foire-aux-questions) before reuse. |
| [France Éducation international: DELF B2](https://www.france-education-international.fr/en/diplome/delf-tout-public/niveau-b2) and [updated DELF/DALF assessment grids](https://www.france-education-international.fr/en/actualites/lettre-fei/2022-10/delf-dalf-de-nouvelles-grilles-pour-une-evaluation-au-plus-pres-des-competences-des-candidats) | Optional general CEFR-exam benchmark for four-skill assessment and rubric design. | Exam specifications/rubrics are references, not permission to copy exam prompts or claim Parlez results are official. Keep DELF distinct from Canada tests. |

### 5.2 Strongest identified reuse candidates — verify the exact item and attribution

| Resource | License/use | Decision |
| --- | --- | --- |
| [COERLL French materials catalog](https://coerll.utexas.edu/coerll/materials/language/french/) — [Français interactif](https://www.laits.utexas.edu/fi/) | COERLL lists the curriculum as CC BY. The source's adoption page lists CC BY 3.0, while a fourth-edition book PDF indicates CC BY 4.0. It includes first-year curriculum, phonetics, grammar, vocabulary, audio/video and exercises. | Best starting OER for comparing lesson scope and adapting eligible text/material. **Resolve the edition/license discrepancy at asset level**; some media may have separate rights. Attribute the authors/source/license and state changes. Its U.S.-college/France context should not be treated as a finished adult/Canada syllabus. |
| [Tex's French Grammar](https://www.laits.utexas.edu/tex/) | COERLL lists this reference grammar and interactive exercises as CC BY. | Candidate for attributed, selective adaptation after checking the specific page and any attached media. Use grammar as support for a task rather than importing the book's grammar-first structure. |
| [Les Conversations Mises à Jour](https://cmaj.coerll.utexas.edu/) | COERLL lists this intermediate/advanced conversation collection as CC BY-SA. | Candidate for appropriately attributed use only if the ShareAlike obligations are compatible with the intended product/content licensing. Check recording and speaker rights per asset. |
| [Enhancing French Skills](https://sites.la.utexas.edu/enhancing-french-skills-new/) | COERLL lists CC BY-NC-SA. | Useful pedagogical reference, but **not for commercial redistribution/adaptation** without additional written permission. |
| [Français inclusif: French 102](https://boisestate.pressbooks.pub/french102/front-matter/credits/) | The book is CC BY-NC-SA 4.0 except where otherwise noted; its credits identify reused content and separate audio rights. | Do not incorporate into a paid product without additional rights. Its credits are also a useful example of why each embedded asset needs its own provenance record. |
| [Tatoeba sentence downloads](https://tatoeba.org/en/downloads) and [terms](https://tatoeba.org/en/terms_of_use) | Sentence text is generally CC BY 2.0 FR; a subset is CC0. Audio is licensed per contributor, separately from the sentence. | A possible source for carefully selected sentence-level examples, not a calibrated syllabus or automatically vetted answer key. Maintain author attribution for CC BY text; proofread/quality-check each selected sentence. Do not reuse audio with no compatible license or unclear rights. |

### 5.3 Free and useful for learners, but link out rather than ingest

| Resource | Learning value | Rights boundary |
| --- | --- | --- |
| [TV5MONDE Apprendre](https://apprendre.tv5monde.com/en/collection-all) and [level guide](https://support-apprendre.tv5monde.com/en/support/solutions/articles/61000298790-what-do-the-exercise-levels-correspond-to-) | Large collection of free, CEFR-labeled A1–B2 activities based on video/authentic media; helpful as a practice recommendation and level-design comparator. | The [current TV5MONDE terms](https://www.tv5monde.com/la-chaine/conditions-generales-d-utilisation) prohibit copying, reproducing, adapting or transferring content to a third-party site without prior written permission, including commercial use and certain AI/ML uses. Link out; do not mirror, scrape, train on, or embed its media/exercises without written clearance. |
| [Le français facile avec RFI](https://francaisfacile.rfi.fr/en/), [exercises](https://francaisfacile.rfi.fr/en/exercices/) and [Journal en français facile](https://francaisfacile.rfi.fr/en/podcasts/) | Free level-organized listening exercises, authentic audio, transcripts and current-affairs practice; useful optional learner links, especially at A2–B2. | Free online access is not a redistribution license. RFI's rebroadcast terms are limited to approved radio partnerships, and other uses require a specific request. Link out; do not import audio, transcripts, questions or graphics without permission. |
| [Mozilla Common Voice terms](https://commonvoice.mozilla.org/terms/fr.html) and [dataset page](https://commonvoice.mozilla.org/en/datasets) | Potential speech data for research/prototyping; not a CEFR-graded course or exam bank. | The terms effective 31 October 2025 describe CC0 datasets available exclusively through Mozilla Data Collective and ask users not to publish, distribute or mirror datasets on other services. Treat it as **not cleared for in-app redistribution**; use only after checking the current release terms and obtaining clarification if needed. |
| [OER Commons](https://oercommons.org/) and institutional OER catalogs | Discover more candidate textbooks and activity banks. | A catalog entry is not a license grant. Follow through to the creator's page and confirm the exact asset, license/version, attribution and embedded media before use. |

### 5.4 Learning-design evidence

- Kim & Webb, [“The Effects of Spaced Practice on Second Language Learning: A Meta-Analysis”](https://onlinelibrary.wiley.com/doi/10.1111/lang.12479), *Language Learning* (2022), analyzed 48 experiments with 3,411 learners and found a medium-to-large benefit of spacing for L2 learning/retention. Longer spacing improved delayed retention more than shorter spacing; equal and expanding schedules were statistically equivalent overall. This supports planned returns to vocabulary and grammar, not a claim that one fixed spaced-repetition schedule works for every learner.
- The Council of Europe's action-oriented approach and CLIC's adult-learning framework both support designing around meaningful tasks; CLIC explicitly places grammar in service of communication. Use them with professional review, not as permission to reproduce their lesson content.

## 6. Reuse and provenance policy

Before any outside material enters a course file or database, create a content-register entry containing:

```text
asset_id
asset_title / author / rights holder
exact_source_url and access date
license name + version (or permission reference)
what is being reused (text, image, audio, video, prompt, metadata)
attribution text and required license link
changes/adaptation made
commercial-use and ShareAlike/NC/ND compatibility review
CEFR/NCLC mapping rationale (Parlez-authored; not copied descriptor text)
reviewer, review date and source/version check date
```

If the record is incomplete, use an external link or create an original replacement. Keep the license of text, recording, image, transcript and dataset separate when they come from different contributors. Do not treat a provider's free sample, a search snippet, a user-uploaded copy or an unmarked web page as permission. Maintain a dated review of exam formats and external link availability.

## 7. Assessment and data-model implications

The current `Course` / `Unit` / `Lesson` model should grow only when the curriculum specification is ready, but the target content contract should support:

```text
Course: level, version, status, original level outcomes, source references
Unit: mission, outcome IDs, skill/mode coverage, prerequisites, capstone, rubric
Lesson: outcome IDs, input type, language resources, practice, feedback mode,
        planned retrieval links, accessibility, estimated time
Asset: source, exact license, attribution, changes, clearance/review status
Assessment: skill, task type, criteria, rubric version, human/automated status,
            version of the relevant exam specification (if exam-specific)
```

Assessment should show a **profile by skill**, not only one overall badge. Use closed-answer scoring only for well-formed closed items. Use transparent, criteria-based feedback for speaking/writing and label it as practice. Human review is needed before making proficiency or readiness claims. Avoid reproducing official assessment grids unless rights permit; write a Parlez rubric and validate it with qualified French-language educators.

## 8. Recommended implementation sequence and release gates

1. **Keep A2–B2 disabled and add a content-integrity gate.** The application currently keeps them unpublished by default; before an admin can enable them, reject malformed text/IDs and require the repair review to pass. Repair or replace the 450 known truncated strings and migrate the B1 ID without orphaning progress/settings. Do not restore from the `.bak` files without the same checks.
2. **Approve the source/use policy and map.** Confirm product licensing posture and whether the Canadian pathway should prioritize newcomer, workplace, general, or exam-specific contexts. No source downloads are needed for this approval.
3. **Version the course model and audit IDs.** Record current lesson/unit IDs and usage before moving content. Add outcomes, skill/mode tags, capstones, review links and asset provenance without breaking saved progress or admin availability settings.
4. **Rebuild A1 first.** Map its existing 24 lessons onto the mission spine, retain worthwhile original content, identify gaps, add missing tasks/phonology/review and have it reviewed. Keep A1 default until this release passes review.
5. **Create A2–B2 as new drafts.** Build coherent outcomes and lesson sequences rather than stretching one lesson per unit. Do not activate until each level has a balanced task sequence and an integrated level-end assessment.
6. **Rebuild Canada exam preparation separately.** Replace generic/stale metadata with versioned TEF Canada and TCF Canada tracks. Add original task practice for all four skills, with exact timed formats and separate unofficial feedback rubrics.
7. **Pilot and revise.** Test with adult learners at each intended level and with qualified FLE reviewers. Use results to revise clarity, accessibility, task difficulty and duration; do not infer certification from course completion or a small quiz.

**Minimum publish gate for a level:**

- Every unit has original measurable outcomes tied to a justified CEFR reference; Canada/NCLC mapping is separately documented where needed.
- Automated, field-aware data checks reject malformed/truncated strings, invalid or duplicate IDs, broken references, and missing required prompts/outcomes before content can be published.
- Across the level, reception, production, interaction and mediation are taught and assessed with evidence—not inferred from lesson titles.
- Each unit has a realistic final task, and the level has a cumulative capstone plus cumulative retrieval/review.
- Pronunciation/phonology, intelligibility, register, clarification/repair and accessibility have an explicit sequence.
- Every external asset has complete rights/provenance and attribution; there are no uncleared exam items, media or NC/ND materials in a paid course.
- Two independent qualified French FLE reviewers have checked the content and rubric; factual/Canadian-context details have an identified reviewer.
- Public copy accurately distinguishes practice from a test, states availability, avoids price/immigration promises, and does not claim official CEFR/NCLC/exam certification.

## 9. Standing caveats to retain

- Course availability is not equal across levels: only A1 is enabled by default; higher-level content remains subject to review.
- Provider specifications, sample resources and IRCC rules can change. The formats above were checked on 25 October 2026; verify them again before each release and direct learners to official provider/IRCC pages.
- Parlez practice results are not official CEFR, NCLC, TEF or TCF scores, and are not an immigration assessment or advice. Do not promise a particular level, test score, course completion time, employment outcome or immigration result.
- The existing **US$4.99/month** figure in [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) is a planning assumption, not a live subscription price or validated willingness-to-pay. Re-check price, taxes, seller/payment availability and included usage before launch; do not make unvalidated affordability or competitor claims.
- Free access is not reuse permission. Use original Parlez work, rights-cleared assets, or an external link unless commercial adaptation rights are documented.
