# Parlez Chatbot — Complete Project Record

## Overview

**Parlez — French AI Tutor** is a comprehensive French language learning chatbot built as a Python FastAPI application. It runs on port 8000 via Docker and uses the NVIDIA NIM API (Nemotron 3 Nano Omni) for AI-powered tutoring.

The chatbot is a subdirectory (`chatbot/`) of a larger Next.js French learning app (`parlez-french/`), but operates independently.

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn
- **AI**: NVIDIA NIM API (`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`) via OpenAI-compatible client
- **Frontend**: Vanilla HTML/CSS/JS (no framework), served as static files
- **Storage**: JSON files (`users.json` for all user data)
- **Auth**: bcrypt password hashing + PyJWT (HS256, 72h expiry)
- **Docker**: Single container, volumes for `data/` and `static/`
- **Fonts**: Inter (UI), Playfair Display (French display text)

---

## What Was Built

### 1. AI Tutor System (`engine/__init__.py`)

The core AI conversation engine with:
- **Mode detection**: Automatically detects what the user wants (lesson, vocabulary, grammar, test, conversation, pronunciation, general)
- **Level-adaptive system prompts**: A1-C1 CEFR levels with different English/French ratios
- **Structured output format**: AI outputs interactive code blocks (```quiz, ```flashcards, ```vocabulary, ```conjugation, ```dialogue, ```exercise, ```practiceset) that JS parses into interactive UI components
- **Lesson context injection**: When studying a lesson, the AI gets the full lesson data (vocab, grammar, conjugation, dialogues) injected into context
- **Adaptive difficulty**: System prompt dynamically adjusted based on student performance

### 2. Course System (5 CEFR Levels)

| Level | Units | Lessons | Vocab | Grammar | Exercises | Dialogues |
|-------|-------|---------|-------|---------|-----------|-----------|
| A1 | 6-9 | 24 | 352 | 43 | 167 | 114 |
| A2 | 6 | 7 | 116 | 15 | 39 | 53 |
| B1 | 5 | 6 | 76 | 13 | 32 | 39 |
| B2 | 5 | 6 | 78 | 12 | 32 | 38 |
| C1 | 5 | 6 | 62 | 6 | 13 | 12 |

- **A1**: Ported from TypeScript (Inspire textbook series) via regex converter (`convert_courses.py`)
- **A2/B1/B2**: Converted from TypeScript via same converter
- **C1**: Created from scratch (Advanced Argumentation, Literary/Journalistic French, Academic Writing, Cultural Mastery, Spoken Fluency)
- **Lesson structure**: Each lesson has vocabulary (with IPA, examples, categories), grammar rules, conjugation tables, dialogues, exercises, and cultural notes
- **Teaching order**: Vocabulary → Grammar → Conjugation → Dialogue → Exercises → Cultural Note

**Converter script** (`convert_courses.py`): Reads TypeScript files from the main Next.js app's `src/lib/courses/`, extracts data via regex, outputs Python dataclasses. Handles edge cases: `json.dumps(None)` → `"null"`, exercise IDs with `-e`/`-a` suffixes, conjugation IDs with `-conj-`.

### 3. Exercise Engine (`engine/exercises.py`)

14 exercise types with interactive UI:
1. `multiple_choice` — Pick the correct answer
2. `fill_blank` — Type the missing word
3. `translate_to_fr` — Translate English to French
4. `translate_to_en` — Translate French to English
5. `true_false` — Interactive true/false buttons
6. `reorder` — Drag/click words into correct order
7. `matching` — Match pairs (French ↔ English)
8. `word_bank` — Pick words from a word bank to build sentences
9. `dictation` — Listen and type what you hear
10. `conjugation` — Fill in the correct verb form
11. `article_choice` — Pick the correct article (le/la/l'/les)
12. `pronoun_replace` — Replace nouns with pronouns
13. `transformation` — Transform sentence structure
14. `short_answer` — Free-text answer

**Answer checking**: Accent-insensitive French text normalization (strips accents, punctuation, case).

### 4. Flashcard System (`engine/flashcards.py`)

- **SM-2 spaced repetition algorithm**: interval = previous_interval × ease_factor (max 30 days)
- **Quality ratings**: 1 (Again) to 5 (Easy) adjust ease_factor and interval
- **Card states**: New → Learning → Mature (based on interval thresholds)
- **Review scheduling**: Cards due for review based on next_review timestamp
- **Auto-creation**: Flashcards auto-created from vocabulary exercises
- **Per-user decks**: Each user has their own flashcard collection

### 5. Practice Engine (`engine/practice.py`)

- **Vocabulary quizzes**: Bidirectional (FR→EN and EN→FR) multiple choice
- **Conjugation drills**: Verb conjugation across tenses
- **Word of the day**: Random vocabulary pick from user's learned words
- **Lesson practice**: Generate exercises from lesson data
- **Vocabulary categorization**: Organize words by theme

### 6. Exam Simulation (TEF/TCF)

- **270 questions total**: 135 TEF + 135 TCF
- **Sections**: Reading, Listening, Vocabulary/Grammar (TEF) or Language Structures (TCF)
- **Practice sets**: 3 sets per section, 15 questions each (in `mock_tests/expanded_data.py`)
- **Timed test mode**: Configurable timer per section
- **Question navigation**: Jump between questions, mark answered/unanswered
- **Audio playback**: Listen to audio for listening sections
- **Level estimation**: A1-C1 based on score
- **Results**: Score ring, per-level breakdown, question review with explanations

### 7. Adaptive Difficulty Engine (`engine/adaptive.py`)

Analyzes student performance in real-time:
- **Weak area detection**: <60% accuracy with ≥3 attempts = weak area
- **Strong area detection**: ≥80% accuracy = strong area
- **Trend analysis**: Improving/declining/stable based on recent vs older performance
- **Dynamic adjustments**:
  - French/English ratio adjusts ±15% from level base (A1=0.4, A2=0.5, B1=0.65, B2=0.8)
  - Practice count: 3-5 exercises per concept
  - Complexity: simple/standard/challenging
- **System prompt injection**: `build_adaptive_prompt_addition()` adds performance context to AI prompt
- **API**: `GET /api/adaptive/analysis` returns full analysis for frontend

### 8. Content Ingestion (`engine/content_ingestion.py`)

Paste French text → extract learning material:
- **Vocabulary extraction**: Uses level-specific word dictionaries (A1-B2)
- **Flashcard auto-creation**: Extracted vocab added to user's flashcard deck
- **Comprehension quiz**: Generated from extracted content (fill_blank, translate_to_fr types)
- **API**: `POST /api/content/ingest` accepts `{text, level}` → returns vocabulary + flashcards + quiz + summary

### 9. Writing Correction (`engine/writing.py`)

AI-powered French writing correction:
- **Structured correction**: Grammar errors (red), vocabulary suggestions (blue), style improvements (green)
- **Scoring**: Overall correctness score
- **Strengths/improvements**: Identifies what's good and what needs work
- **Inline annotations**: Color-coded HTML output
- **API**: `POST /api/writing/correct` accepts `{text, level}` → returns structured corrections

### 10. Authentication System

- **bcrypt** password hashing (not plaintext)
- **PyJWT** tokens (HS256, 72-hour expiry)
- **Per-user data isolation**: All data stored per-user in `users.json`
- **Auth flow**: signup → JWT in localStorage (`parlez_token`) → Bearer header on all API calls → 401 auto-logout
- **Endpoints**: `POST /api/auth/signup`, `POST /api/auth/login`, `GET /api/auth/me`

### 11. Collaboration Features

- **Comments/Notes**: `POST /api/comments`, `GET /api/comments`, `DELETE /api/comments/:id`
- **Share links**: `POST /api/share` generates shareable link, `GET /api/share/:id` retrieves
- **Export**: `POST /api/export` → markdown or JSON format

### 12. Progress Tracking

- **XP system**: Earn XP from exercises, flashcard reviews, chat messages
- **Streak tracking**: Daily streak with best streak
- **Per-user stats**: lessons_completed, tests_taken, level, last_active
- **Exercise history**: Track all exercise attempts with accuracy per type
- **Test history**: Store all mock test results with detailed breakdown

---

## API Endpoints (all require auth unless noted)

### Auth
- `POST /api/auth/signup` — Create account
- `POST /api/auth/login` — Login, returns JWT
- `GET /api/auth/me` — Get current user info
- `POST /api/auth/logout` — Logout

### Chat
- `POST /api/chat` — Send message to AI tutor (auto-detects mode)
- `GET /api/conversations` — List user's conversations
- `GET /api/conversations/:id` — Get conversation with messages
- `DELETE /api/conversations/:id` — Delete conversation
- `PUT /api/conversations/:id/title` — Rename conversation

### Courses
- `GET /api/courses` — List all courses
- `GET /api/courses/:level` — Get course details
- `GET /api/scenarios` — List conversation scenarios

### Practice
- `POST /api/practice/vocab-quiz` — Generate vocab quiz
- `POST /api/practice/conj-quiz` — Generate conjugation drill
- `GET /api/practice/word-of-day` — Get word of the day
- `POST /api/practice/lesson/:level/:lessonId` — Lesson exercises

### Flashcards
- `GET /api/flashcards/due` — Get cards due for review
- `GET /api/flashcards/stats` — Get deck statistics
- `POST /api/flashcards/:id/review` — Rate a flashcard

### Exercises
- `POST /api/exercises/check` — Check exercise answer

### Exam Simulation
- `GET /api/exam/sets/:testType` — Get exam format and practice sets
- `GET /api/exam/questions/:testType/:sectionId/:setNum` — Get practice set questions
- `POST /api/exam/submit/:testType/:sectionId/:setNum` — Submit test answers
- `GET /api/exam/stats/:testType` — Get test history stats

### Adaptive
- `GET /api/adaptive/analysis` — Get performance analysis

### Content
- `POST /api/content/ingest` — Ingest French text content

### Writing
- `POST /api/writing/correct` — Get writing correction

### Progress
- `GET /api/progress` — Get user progress

### Collaboration
- `POST /api/comments` — Add comment
- `GET /api/comments` — Get comments
- `DELETE /api/comments/:id` — Delete comment
- `POST /api/share` — Create share link
- `GET /api/share/:id` — Get shared conversation
- `POST /api/export` — Export conversation

---

## Frontend Architecture

### View Management (CRITICAL)

The UI has TWO mutually exclusive views in the main content area:

1. **`#chatView`** — The chat interface (messages + input). ONLY for AI conversations.
2. **`#toolView`** — Dedicated panel for non-chat activities. Renders into `#toolContent`.

**Functions**:
- `showToolView(title, html)` — Hides chatView, shows toolView, injects HTML
- `showChatView()` — Hides toolView, shows chatView
- `#btnBackToChat` — Button to return to chat

**ALL non-chat activities MUST use `showToolView()`**:
- Vocab Quiz, Conjugation Drill, Flashcard Review
- Word of the Day, Learning Analysis
- TEF/TCF Practice, Test History
- Content Ingestion, Lesson Practice

**`addMessage()` is ONLY for**: AI chat messages, conversation history, share/export feedback, writing correction in chat.

### Markdown Parser

`parseMarkdown()` in app.js handles:
- Headers, bold, italic, code blocks
- Interactive code block parsing: ```vocabulary, ```conjugation, ```dialogue, ```quiz, ```exercise, ```practiceset
- Each type has a renderer function that generates interactive HTML
- Markdown tables → `<table>` HTML conversion
- Inline TTS buttons for French text

### Exercise Rendering

`renderExercise(ex, data)` generates HTML for all 14 exercise types:
- Uses inline `onclick` handlers referencing `window.*` functions
- `window.checkQuizAnswer(btn)` — Check MCQ answer
- `window.checkExercise(id, input)` — Check fill-in/translation
- `window.addReorderWord(id, chip)` — Add word to reorder area
- `window.checkReorder(id)` — Check reorder answer
- `window.checkMatching(id, pairCount)` — Check matching pairs
- `window.speakText(text)` — TTS playback

### CSS Design System

- **Primary**: #7C2D3F (deep burgundy)
- **Secondary**: #C19A4B (gold)
- **All colors**: CSS custom properties for theming
- **Light theme**: Default (user preference)
- **Responsive**: Sidebar collapses on mobile

---

## Data Storage

All user data in `data/users.json` (single file, all users):

```json
{
  "user_id": {
    "id": "uuid",
    "username": "string",
    "password_hash": "bcrypt_hash",
    "name": "string",
    "level": "A1",
    "created_at": "ISO timestamp",
    "conversations": { "conv_id": { "id", "title", "messages": [], "created_at" } },
    "progress": { "xp", "streak", "best_streak", "lessons_completed", "tests_taken", "level", "last_active" },
    "flashcards": [{ "id", "front", "back", "meta", "interval", "ease_factor", "repetitions", "next_review" }],
    "exercise_history": [{ "exercise_id", "type", "answer", "correct", "level", "timestamp" }],
    "test_results": [{ "testType", "sectionId", "setNum", "score", "correct", "total", "durationSec", "level", "details", "takenAt" }]
  }
}
```

Legacy files in `data/` (mostly unused now): `conversations.json`, `progress.json`, `flashcards.json`, `exercise_history.json`, `test_results.json`, `shared.json`, `comments.json`, `skills.json`, `connectors.json`, `projects.json`, `streaks.json`, `user.json`.

---

## Docker Setup

```yaml
# docker-compose.yml
services:
  chatbot:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    volumes:
      - ./data:/app/data        # Persistent user data
      - ./static:/app/static    # Live frontend editing (no rebuild needed)
    restart: unless-stopped
```

**Commands**:
- `docker compose down && docker compose build --no-cache && docker compose up -d` — Full rebuild
- `docker compose down && docker compose up -d` — Restart (with volume-mounted static files)
- `docker logs chatbot-chatbot-1` — Check logs
- Hard refresh `Ctrl+Shift+R` after static file changes

---

## Known Issues / TODO

1. **Tool view content rendering bug**: After wiring all practice functions to `showToolView()`, the user reports the tool view appears but shows empty content. Root cause not yet identified — `showToolView` is called, `toolView` shows, but `toolContent.innerHTML` may not be rendering visually. Possibly a CSS layout issue or a JS execution order problem. The functions use `document.getElementById()` directly (not const references) to avoid null issues.

2. **Writing correction in chat**: `correctMyWriting()` still uses `addMessage()` instead of `showToolView()` — needs wiring.

3. **Session persistence for non-chat activities**: Practice session results not persisted when navigating away.

4. **Chat title renaming**: Activities should rename the chat title but this isn't working consistently.

5. **Exercise interactive rendering**: All `window.*` functions exist and HTML generation is correct, but some exercise types (matching, reorder, word bank, dictation, conjugation) may not be fully interactive in the browser — needs live testing.

---

## Session History

### Session 1 (2026-07-01)
- Built complete AI tutor system with mode detection
- Created course system (A1-C1) with 684 vocab items, 89 grammar rules, 283 exercises
- Built exercise engine (14 types), flashcard system (SM-2), practice engine
- Added auth system (bcrypt + JWT), per-user data isolation
- Built TEF/TCF exam simulation (270 questions)
- Added collaboration features (comments, share, export)
- Built Phase 6 features: Adaptive Difficulty, Content Ingestion, Writing Correction

### Session 2 (2026-07-02)
- Fixed exercise rendering for matching/reorder/word bank/dictation/conjugation
- Added markdown table rendering
- Separated activities from chat (started tool view pattern)
- Added voice toggle, logout button
- **In progress**: Wired all practice/test functions to `showToolView()` — 15 functions updated, but user reports empty content in tool view. Bug under investigation.

---

## Key Files Quick Reference

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | ~1300 | All API routes, auth, AI integration |
| `engine/__init__.py` | ~300 | AI system prompt, mode detection |
| `engine/adaptive.py` | ~150 | Adaptive difficulty |
| `engine/content_ingestion.py` | ~150 | French content processing |
| `engine/writing.py` | ~150 | Writing correction |
| `engine/practice.py` | ~200 | Quiz/drill generation |
| `engine/flashcards.py` | ~150 | SM-2 spaced repetition |
| `engine/exercises.py` | ~200 | Exercise grading (14 types) |
| `courses/data.py` | ~50 | Course registry, C1 course |
| `courses/types.py` | ~100 | Dataclass definitions |
| `courses/a1.py` | ~1500 | A1 course data |
| `courses/a2_course.py` | ~500 | A2 course data |
| `courses/b1_course.py` | ~500 | B1 course data |
| `courses/b2_course.py` | ~500 | B2 course data |
| `mock_tests/data.py` | ~200 | Test definitions |
| `mock_tests/expanded_data.py` | ~2000 | Expanded question banks |
| `static/index.html` | ~250 | SPA HTML |
| `static/app.js` | ~2000 | Frontend logic |
| `static/styles.css` | ~2000 | All CSS |
| `convert_courses.py` | ~200 | TS→Python converter |
