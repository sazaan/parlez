# Curriculum source register

Status: living document · research checked **2026-11-24** · re-verify exam facts every 90 days.

## 0. Critical legal boundary (read first)

**Parlez cannot reproduce real or past TEF/TCF exam questions.** CCI Paris Île-de-France and France Éducation international reserve copyright in their sample booklets, answer keys and audio; Canadian *Copyright Act* s.3/s.29 and French CPI art. L.122-4 point the same way, and exam-board precedent (AQA; *Chicago Bd. of Education v. Substance*) treats past papers as protected. What we **may** do:

- use published **task specifications** (formats, timings, word counts, skill descriptors) — these are facts;
- write **original items** in those formats, with our own texts, audio and rubrics;
- **link** to official samples (plain hyperlinks, with attribution) — never mirror PDFs/audio or embed them behind our product;
- state clearly that results are practice accuracy, not official scores, CEFR/NCLC levels, or immigration evidence.

Full source: the research in `docs/INTERACTIVE_CURRICULUM_PHASES.md` and the disclosure in `static/legal.html`.

This register separates **authoritative references**, **reusable materials**, and **link-only resources**. Parlez publishes original practice content. We do not host or reproduce past exam papers or official sample PDFs. See `docs/PROJECT_OVERVIEW.md` and `docs/CURRICULUM_REDESIGN.md` for product research and the earlier audit.

## 1. Authoritative references (link, don't copy)

| Topic | Source | Use |
| --- | --- | --- |
| CEFR framework and descriptors | [Council of Europe](https://www.coe.int/en/web/common-european-framework-reference-languages/introduction-and-context) and [Companion Volume 2020](https://rm.coe.int/cefr-companion-volume-with-new-descriptors-2018/1680787989.pdf) | Outcome design only. CoE does not validate others' CEFR claims; our statements are original paraphrases. |
| Express Entry language tests and score tables | [IRCC — language testing](https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/documents/language-requirements/language-testing.html) | NCLC equivalencies, validity rules, accepted tests. Source of truth. |
| TCF Canada | [France Éducation international](https://www.france-education-international.fr/test/tcf-canada) and [official samples](https://www.france-education-international.fr/test/exemples-epreuves-tcf?langue=en) | Format facts and sample links. |
| TEF Canada | [Le français des affaires / CCI Paris Île-de-France](https://www.lefrancaisdesaffaires.fr/en/candidate/test-evaluation-francais/tef-canada/presentation/) | Format facts, attestation guidance, preparation links. |
| Canada francophone admissions | [IRCC francophone immigration](https://www.canada.ca/en/immigration-refugees-citizenship/campaigns/francophone-immigration-outside-quebec/francophone-immigration-express-entry.html) | Market context only; never an outcome promise. |

## 2. Reusable / open materials (attribution required)

- **COERLL** resources with a verified CC BY licence — may be adapted with attribution; record the exact version and licence in `ContentProvenance`.
- **TV5MONDE Apprendre** — thousands of graded A1–B2 exercises from authentic video; its TCF simulator questions are FEI-validated but **do not lead to an official certificate**. Link out; don't rehost.
- **RFI Savoirs / Le Français facile** — graded news and exercises with transcripts. Link out.
- **Le Point du FLE** — directory of FLE resources for discovery and QA, not a source to hot-link.

## 3. Link-only (free to access, not licensed for reuse)

- Official TEF/TCF sample PDFs and past papers (FEI, CCI, Hachette, CLE).
- Commercial coursebooks used as task-design models: *Inspire* (AF Kathmandu), *Édito*, *Cosmopolite*, *Grammaire progressive du français*, *Bescherelle*, *Assimil*, *ABC TEF*, *Réussir le TCF*, Hachette's 2023+ TEF workbook.
- Paid platforms: PrepMyTEF, Kwiziq, Lawless French (reference only).

## 3b. Publisher series as structural models (researched 2026-11-24)

All are © their publishers — **structure only, never wording, exercises, audio or images**:

| Series | Levels | Structural lesson to borrow |
| --- | --- | --- |
| **Inspire** (Hachette) | A1–B2 | Direct A1/A2 template: 12-page units, 3 learning lessons + *Techniques pour…* + *S’entraîner* + *Faites le point*, DELF prep every 2 units, TV5MONDE video stitches. |
| **Édito** (Didier) | A1–C1 | Best B1/B2 argumentation model: *Échauffement → Fonctionnement → Entraînement*, phonetics every unit, *Culture, Cultures*, *Atelier-médiation*, RFI link + quiz. |
| **Cosmopolite** (Hachette) | A1–C1 | Project/mediation model: two projects per dossier, `Focus Langue`, `Expressions utiles pour…`, `Apprenons ensemble !`. |
| **Adomania** / **Totem** (Hachette) | A1–B1 | Video-first hook, continuing fiction, *Faits et gestes* (non-verbal culture), collective final task. |
| **Alter Ego+** (Hachette) | A1–B2 | `Point Langue`, `Aide-mémoire` speech-act toolboxes, project per dossier, DELF pages. |

Recurring unit skeleton to re-implement in Parlez's own words: **opening contract → trigger documents → global then detailed comprehension → inductive grammar discovery → vocabulary + phonetics → culture note → drills → mediation/strategy → final task → bilan/self-evaluation**, with spiral recycling and a four-skill check every second unit.

**Cleanest reusable open content:** COERLL *Français interactif* and *Tex’s French Grammar* (**CC BY** — commercial adaptation allowed with attribution), *Grammaire Ouverte*, *Tout un Monde*, *Le littéraire dans le quotidien*. Avoid **CC BY-NC(-SA)** unless Parlez is non-commercial; **CC BY-SA** is viral. TV5MONDE *fiches* may be adapted with a visible credit; their videos may be iframe-embedded but not rehosted. RFI and Le Point du FLE are link-only.

Attribution template: *“Adapted from Français interactif, Blyth/Kelton/Guilloteau, COERLL, University of Texas at Austin, CC BY 4.0. Pedagogical sequence inspired by Inspire (Hachette FLE) and Édito (Didier).”*

## 4. Authoring rules

1. Every lesson, unit and course carries a `ContentProvenance` record: author, licence, source links, version, review state and dates.
2. `review_state` is editorial (`draft` → `practice` → `reviewed`) and is **not** a public proficiency credential.
3. Exam-related content records `exam_format_version` and `verified_on`; re-verify every 90 days and after any owner announcement.
4. Express Entry uses the **"Équivalence ancien score"** column on the TEF attestation. Never present the `/699` column as the Express Entry score.
5. Use CEFR-aligned wording ("based on CEFR can-do descriptors", "practises the format of TCF Canada"), never "CEFR-certified", "official TEF prep" or "NCLC-certified".
6. Keep a claims register: every public claim must have an evidence link in this file or in `docs/PROJECT_OVERVIEW.md`.
