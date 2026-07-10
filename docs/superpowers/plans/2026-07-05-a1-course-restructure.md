# A1 French Course Restructure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `courses/a1_course.py` into an original, copyright-safe A1 curriculum aligned with CEFR A1, DELF A1, TCF, and TEF frameworks.

**Architecture:** Keep the existing `Course → Unit → Lesson` data model. Replace only the content of A1. Archive the old file. Add one new test to verify the restructured course loads and exposes the expected units.

**Tech Stack:** Python 3.12, Pydantic dataclasses in `courses/types.py`, no new dependencies.

---

## File structure

| File | Responsibility |
|---|---|
| `courses/a1_course.py` | New A1 course data (will be rewritten) |
| `courses/a1_course_legacy.py` | Archive of the old A1 course (renamed, not imported) |
| `courses/data.py` | Aggregates all courses; no changes expected |
| `courses/types.py` | Schema definitions; no changes expected |
| `tests/test_courses.py` | New test file verifying course structure loads |

---

## Module overview

| Task | Module | Title | Lessons to create |
|---|---|---|---|
| 2 | M1 | Premiers contacts | Greetings; alphabet; numbers 0–20 |
| 3 | M2 | Mon identité | Personal identity; nationality; professions |
| 4 | M3 | Ma famille et mes proches | Family; descriptions; pets |
| 5 | M4 | Ma journée | Time; daily routine; weather |
| 6 | M5 | En ville | Places; directions; transport |
| 7 | M6 | Manger et boire | Food; drink; café/restaurant |
| 8 | M7 | Chez moi | Rooms; furniture; housing |
| 9 | M8 | Projets et loisirs | Hobbies; weather; dates; near future |

---

## Task 1: Archive old A1 course

**Files:**
- Rename: `courses/a1_course.py` → `courses/a1_course_legacy.py`
- Modify: `courses/data.py` (if it imports `a1_course` by name; verify it still works)
- Test: `tests/test_courses.py` (will be created in Task 10)

- [ ] **Step 1: Rename the file**

```bash
cd /home/sajjan/sajjan/parlez-french/chatbot
mv courses/a1_course.py courses/a1_course_legacy.py
```

- [ ] **Step 2: Create empty new file**

```bash
touch courses/a1_course.py
```

- [ ] **Step 3: Verify imports**

Check `courses/data.py` and `courses/__init__.py` still import from `.a1_course`. The new file will be filled in later tasks.

- [ ] **Step 4: Commit**

```bash
git add courses/a1_course.py courses/a1_course_legacy.py
git commit -m "chore: archive legacy A1 course and create empty restructure file

Co-Authored-By: Kimchi <noreply@kimchi.dev>"
```

---

## Task 2: Write Module 1 — Premiers contacts

**Files:**
- Modify: `courses/a1_course.py` (write the `a1_course = Course(...)` variable)
- Test: `tests/test_courses.py`

Create the `Course` object with level `'A1'` and `units` containing Module 1 only. Module 1 has three lessons.

- [ ] **Step 1: Write the Course header and Module 1 skeleton**

```python
from .types import *

a1_course = Course(
    level='A1',
    title='A1 — Débutant',
    book='Parlez A1',
    description='Original beginner French course. Eight modules covering personal contact, identity, family, daily life, city life, food, home, and future plans. Aligned to CEFR A1 and DELF A1.',
    cefrDescription='Can understand and use familiar everyday expressions and very basic phrases aimed at the satisfaction of needs of a concrete type. Can introduce themselves and others and can ask and answer questions about personal details.',
    color='#2D6A4F',
    units=[
        Unit(
            id='a1-m1',
            title='Module 1 — Premiers contacts',
            titleFr='Module 1 — Premiers contacts',
            theme='First contact with French',
            description='Greet people, introduce yourself, use the alphabet, and count to 20.',
            lessons=[
                # Lesson 1: greetings
                # Lesson 2: alphabet
                # Lesson 3: numbers 0-20
            ],
        ),
    ],
)
```

- [ ] **Step 2: Write Lesson 1 — Greetings and polite expressions**

Create a `Lesson` with:
- `id='a1-m1-l1'`
- `title='Saying Hello and Goodbye'` / `titleFr='Dire bonjour et au revoir'`
- 3–4 objectives about greetings and politeness
- 15–20 `VocabItem`s for greetings, politeness, titles, basics
- 2 `GrammarRule`s: (a) tu vs. vous, (b) time-based greetings
- 1 `ConjugationData` for **être** present tense
- 1 dialogue with 2 original characters
- 4 exercises + 3 activities
- 1 cultural note (original observation)
- `estimatedMinutes=30`

- [ ] **Step 3: Write Lesson 2 — The alphabet and spelling**

- `id='a1-m1-l2'`
- `title='The French Alphabet'` / `titleFr="L'alphabet français"`
- Alphabet letters, spelling phrases, accents
- Grammar: key pronunciation differences, accented letters
- Conjugation: **avoir** present tense
- Dialogue: spelling a name at a reception
- Exercises + activities
- Cultural note

- [ ] **Step 4: Write Lesson 3 — Numbers 0–20**

- `id='a1-m1-l3'`
- `title='Counting to Twenty'` / `titleFr='Compter jusqu\'à vingt'`
- Numbers 0–20, phone numbers, age
- Grammar: using **avoir** for age; masculine/feminine with **un/une**
- Conjugation: review **être** and **avoir**
- Dialogue: giving a phone number and age
- Exercises + activities
- Cultural note

- [ ] **Step 5: Run Python syntax check**

```bash
cd /home/sajjan/sajjan/parlez-french/chatbot
python3 -c "import ast, sys; ast.parse(open('courses/a1_course.py').read())"
```

Expected: no output (success).

- [ ] **Step 6: Commit**

```bash
git add courses/a1_course.py
git commit -m "feat: add original A1 Module 1 — Premiers contacts

Co-Authored-By: Kimchi <noreply@kimchi.dev>"
```

---

## Task 3: Write Module 2 — Mon identité

**Files:**
- Modify: `courses/a1_course.py`

- [ ] **Step 1: Write Lesson 4 — My name and where I am from**

- `id='a1-m2-l1'`
- `title='My Name and Origin'` / `titleFr='Mon nom et mes origines'`
- Vocab: nationalities, languages, countries, verbs *parler*, *venir*, *habiter*
- Grammar: subject pronouns; question words *qui*, *où*, *comment*, *d'où*
- Conjugation: **être** and **avoir** review; **venir** present tense
- Dialogue: meeting at a language exchange

- [ ] **Step 2: Write Lesson 5 — My age and profession**

- `id='a1-m2-l2'`
- `title='Age and Profession'` / `titleFr='Âge et profession'`
- Vocab: professions, numbers 21–60, workplace words
- Grammar: indefinite articles **un/une/des**; professions without article after **être**
- Conjugation: **avoir** for age; **être** for professions
- Dialogue: filling a registration form

- [ ] **Step 3: Write Lesson 6 — Languages I speak**

- `id='a1-m2-l3'`
- `title='The Languages I Speak'` / `titleFr='Les langues que je parle'`
- Vocab: languages, levels (*un peu*, *bien*, *couramment*)
- Grammar: verb **parler**; negation **ne...pas**
- Conjugation: **parler** present tense
- Dialogue: introducing language skills

- [ ] **Step 4: Syntax check and commit**

```bash
python3 -c "import ast, sys; ast.parse(open('courses/a1_course.py').read())"
git add courses/a1_course.py
git commit -m "feat: add original A1 Module 2 — Mon identité

Co-Authored-By: Kimchi <noreply@kimchi.dev>"
```

---

## Task 4: Write Module 3 — Ma famille et mes proches

**Files:**
- Modify: `courses/a1_course.py`

- [ ] **Step 1: Write Lesson 7 — Family members**

- `id='a1-m3-l1'`
- `title='My Family'` / `titleFr='Ma famille'`
- Vocab: family members, marital status
- Grammar: possessive adjectives **mon/ma/mes**, **ton/ta/tes**, **son/sa/ses**
- Conjugation: **avoir** and **être** review
- Dialogue: describing a family photo

- [ ] **Step 2: Write Lesson 8 — Describing people**

- `id='a1-m3-l2'`
- `title='Describing Someone'` / `titleFr='Décrire quelqu'un'`
- Vocab: physical description, character traits, colors
- Grammar: adjective agreement (gender/number); position of adjectives
- Conjugation: **être** + adjective
- Dialogue: describing a missing pet or person

- [ ] **Step 3: Write Lesson 9 — Pets and animals**

- `id='a1-m3-l3'`
- `title='Pets and Animals'` / `titleFr='Les animaux de compagnie'`
- Vocab: common animals, pet care words
- Grammar: definite articles **le/la/les**; partitive preview with **du/des**
- Conjugation: **avoir** for possession
- Dialogue: at the veterinarian or pet store

- [ ] **Step 4: Syntax check and commit**

```bash
python3 -c "import ast, sys; ast.parse(open('courses/a1_course.py').read())"
git add courses/a1_course.py
git commit -m "feat: add original A1 Module 3 — Ma famille et mes proches

Co-Authored-By: Kimchi <noreply@kimchi.dev>"
```

---

## Task 5: Write Module 4 — Ma journée

**Files:**
- Modify: `courses/a1_course.py`

- [ ] **Step 1: Write Lesson 10 — Time and schedule**

- `id='a1-m4-l1'`
- `title='What Time Is It?'` / `titleFr='Quelle heure est-il ?'`
- Vocab: hours, minutes, schedules, days of the week
- Grammar: telling time; **à** + time
- Conjugation: **être** and **avoir**
- Dialogue: making an appointment

- [ ] **Step 2: Write Lesson 11 — My daily routine**

- `id='a1-m4-l2'`
- `title='My Daily Routine'` / `titleFr='Ma routine quotidienne'`
- Vocab: routine verbs, meals, parts of the day
- Grammar: reflexive verbs (**se lever**, **se coucher**, **s'habiller**)
- Conjugation: reflexive verbs in present tense
- Dialogue: morning conversation

- [ ] **Step 3: Write Lesson 12 — Weather and seasons**

- `id='a1-m4-l3'`
- `title='Talking About the Weather'` / `titleFr='Parler de la météo'`
- Vocab: weather expressions, seasons, months
- Grammar: **il fait** + weather; **en** + season/month
- Conjugation: review **faire** present tense
- Dialogue: planning a day based on weather

- [ ] **Step 4: Syntax check and commit**

```bash
python3 -c "import ast, sys; ast.parse(open('courses/a1_course.py').read())"
git add courses/a1_course.py
git commit -m "feat: add original A1 Module 4 — Ma journée

Co-Authored-By: Kimchi <noreply@kimchi.dev>"
```

---

## Task 6: Write Module 5 — En ville

**Files:**
- Modify: `courses/a1_course.py`

- [ ] **Step 1: Write Lesson 13 — Places in the city**

- `id='a1-m5-l1'`
- `title='Places in Town'` / `titleFr='Les lieux en ville'`
- Vocab: shops, services, public buildings
- Grammar: articles **un/une/le/la/les**; prepositions **à** and **de**
- Conjugation: **aller** present tense
- Dialogue: asking where a place is

- [ ] **Step 2: Write Lesson 14 — Directions**

- `id='a1-m5-l2'`
- `title='Asking for and Giving Directions'` / `titleFr='Demander et indiquer le chemin'`
- Vocab: direction words, prepositions of place
- Grammar: prepositions of place (**à gauche**, **à droite**, **tout droit**, **près de**, **loin de**)
- Conjugation: **aller**; imperative for directions
- Dialogue: giving directions to a tourist

- [ ] **Step 3: Write Lesson 15 — Transport and tickets**

- `id='a1-m5-l3'`
- `title='Getting Around'` / `titleFr='Se déplacer'`
- Vocab: transport, tickets, prices
- Grammar: articles contractés (**au**, **à la**, **aux**, **du**, **de la**, **des**)
- Conjugation: **prendre** present tense
- Dialogue: buying a metro ticket

- [ ] **Step 4: Syntax check and commit**

```bash
python3 -c "import ast, sys; ast.parse(open('courses/a1_course.py').read())"
git add courses/a1_course.py
git commit -m "feat: add original A1 Module 5 — En ville

Co-Authored-By: Kimchi <noreply@kimchi.dev>"
```

---

## Task 7: Write Module 6 — Manger et boire

**Files:**
- Modify: `courses/a1_course.py`

- [ ] **Step 1: Write Lesson 16 — Food and drink**

- `id='a1-m6-l1'`
- `title='Food and Drink'` / `titleFr='Nourriture et boissons'`
- Vocab: meals, drinks, common foods, quantities
- Grammar: partitive articles **du/de la/des**; **un peu de / beaucoup de**
- Conjugation: **boire** and **manger** present tense
- Dialogue: talking about preferences

- [ ] **Step 2: Write Lesson 17 — At the café**

- `id='a1-m6-l2'`
- `title='Ordering at a Café'` / `titleFr='Commander au café'`
- Vocab: café items, prices, polite ordering phrases
- Grammar: imperative for ordering; **s'il vous plaît / s'il te plaît**
- Conjugation: **vouloir** and **prendre**
- Dialogue: ordering coffee and pastry

- [ ] **Step 3: Write Lesson 18 — At the restaurant**

- `id='a1-m6-l3'`
- `title='At the Restaurant'` / `titleFr='Au restaurant'`
- Vocab: menu items, courses, dietary words
- Grammar: question formation with **est-ce que**; **du/des** review
- Conjugation: **vouloir**, **prendre**, **aimer**
- Dialogue: a full restaurant conversation

- [ ] **Step 4: Syntax check and commit**

```bash
python3 -c "import ast, sys; ast.parse(open('courses/a1_course.py').read())"
git add courses/a1_course.py
git commit -m "feat: add original A1 Module 6 — Manger et boire

Co-Authored-By: Kimchi <noreply@kimchi.dev>"
```

---

## Task 8: Write Module 7 — Chez moi

**Files:**
- Modify: `courses/a1_course.py`

- [ ] **Step 1: Write Lesson 19 — Rooms and furniture**

- `id='a1-m7-l1'`
- `title='My Home'` / `titleFr='Mon logement'`
- Vocab: rooms, furniture, household objects
- Grammar: prepositions of place; **il y a** for existence
- Conjugation: **être** for location
- Dialogue: showing someone around the apartment

- [ ] **Step 2: Write Lesson 20 — Where things are**

- `id='a1-m7-l2'`
- `title='Where Is It?'` / `titleFr='Où est-ce ?'`
- Vocab: household objects, position words
- Grammar: demonstrative adjectives **ce/cet/cette/ces**
- Conjugation: **être** + prepositions
- Dialogue: looking for lost keys

- [ ] **Step 3: Write Lesson 21 — Renting a room**

- `id='a1-m7-l3'`
- `title='Finding a Place to Live'` / `titleFr='Trouver un logement'`
- Vocab: housing types, rent, amenities
- Grammar: interrogative **combien**, **quel/quelle**
- Conjugation: **coûter**, **avoir** for amenities
- Dialogue: asking about an apartment ad

- [ ] **Step 4: Syntax check and commit**

```bash
python3 -c "import ast, sys; ast.parse(open('courses/a1_course.py').read())"
git add courses/a1_course.py
git commit -m "feat: add original A1 Module 7 — Chez moi

Co-Authored-By: Kimchi <noreply@kimchi.dev>"
```

---

## Task 9: Write Module 8 — Projets et loisirs

**Files:**
- Modify: `courses/a1_course.py`

- [ ] **Step 1: Write Lesson 22 — Hobbies and free time**

- `id='a1-m8-l1'`
- `title='My Hobbies'` / `titleFr='Mes loisirs'`
- Vocab: sports, hobbies, leisure activities, frequency words
- Grammar: verb **faire** + sport/activity; **jouer à / jouer de**
- Conjugation: **faire** and **jouer** present tense
- Dialogue: talking about weekend plans

- [ ] **Step 2: Write Lesson 23 — Dates and celebrations**

- `id='a1-m8-l2'`
- `title='Dates and Celebrations'` / `titleFr='Dates et fêtes'`
- Vocab: months, dates, birthdays, holidays
- Grammar: dates with **le** + number; **quand** questions
- Conjugation: **être** and **avoir** review
- Dialogue: planning a birthday

- [ ] **Step 3: Write Lesson 24 — Future plans**

- `id='a1-m8-l3'`
- `title='My Plans for Next Week'` / `titleFr='Mes projets pour la semaine prochaine'`
- Vocab: future time expressions, travel words
- Grammar: near future **aller + infinitive**
- Conjugation: **aller** present tense + infinitives
- Dialogue: making plans with a friend

- [ ] **Step 4: Syntax check and commit**

```bash
python3 -c "import ast, sys; ast.parse(open('courses/a1_course.py').read())"
git add courses/a1_course.py
git commit -m "feat: add original A1 Module 8 — Projets et loisirs

Co-Authored-By: Kimchi <noreply@kimchi.dev>"
```

---

## Task 10: Add course structure tests

**Files:**
- Create: `tests/test_courses.py`

- [ ] **Step 1: Write the test file**

```python
"""Tests for course data structure and A1 restructure completeness."""

from courses import courses, get_course, course_levels


def test_a1_course_exists():
    course = get_course('A1')
    assert course is not None
    assert course.level == 'A1'


def test_a1_has_eight_modules():
    course = get_course('A1')
    assert len(course.units) == 8


def test_a1_module_ids_are_unique():
    course = get_course('A1')
    ids = [u.id for u in course.units]
    assert len(ids) == len(set(ids))


def test_a1_modules_have_original_titles():
    course = get_course('A1')
    titles = [u.title for u in course.units]
    assert 'Module 1 — Premiers contacts' in titles
    assert 'Module 2 — Mon identité' in titles
    assert 'Module 3 — Ma famille et mes proches' in titles
    assert 'Module 4 — Ma journée' in titles
    assert 'Module 5 — En ville' in titles
    assert 'Module 6 — Manger et boire' in titles
    assert 'Module 7 — Chez moi' in titles
    assert 'Module 8 — Projets et loisirs' in titles


def test_a1_lessons_have_required_fields():
    course = get_course('A1')
    for unit in course.units:
        assert len(unit.lessons) >= 1
        for lesson in unit.lessons:
            assert lesson.id
            assert lesson.title
            assert lesson.titleFr
            assert lesson.vocabulary
            assert lesson.grammar
            assert lesson.dialogue
            assert lesson.exercises
            assert lesson.culturalNote
```

- [ ] **Step 2: Run the tests**

```bash
cd /home/sajjan/sajjan/parlez-french/chatbot
JWT_SECRET=$(openssl rand -hex 32) NVIDIA_API_KEY=dummy venv/bin/python -m pytest tests/test_courses.py -v
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/test_courses.py
git commit -m "test: add course structure tests for A1 restructure

Co-Authored-By: Kimchi <noreply@kimchi.dev>"
```

---

## Task 11: Full regression test

**Files:**
- No file changes; validation only.

- [ ] **Step 1: Run the full test suite**

```bash
cd /home/sajjan/sajjan/parlez-french/chatbot
JWT_SECRET=$(openssl rand -hex 32) NVIDIA_API_KEY=dummy venv/bin/python -m pytest tests/ -q
```

Expected: all tests pass.

- [ ] **Step 2: Check that legacy file is not imported**

```bash
grep -r "a1_course_legacy" courses/ --include="*.py"
```

Expected: no matches (only the archive file should exist).

- [ ] **Step 3: Final commit or wrap-up**

If tests pass, no further commit is needed. If there are mock-test mismatches, create a follow-up task to fix them.

---

## Self-review

- **Spec coverage:** Each module in the design doc maps to a Task 2–9 above. CEFR/DELF/TCF/TEF alignment is embedded in the module themes and lesson competencies.
- **Placeholder scan:** No TODOs or TBDs. Each task includes exact `id`, titles, grammar points, and verbs.
- **Type consistency:** Uses existing `Course`, `Unit`, `Lesson`, `VocabItem`, etc. from `courses/types.py`.
- **Copyright safety:** Explicit rule in Task 2 that all dialogues, examples, vocabulary, and cultural notes must be original.
