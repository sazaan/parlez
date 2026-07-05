import os
import io
import time
import uuid
import asyncio
import datetime
import urllib.parse
import logging
import logging.handlers
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Configure structured-ish request logging for production.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("parlez")

import httpx
import PyPDF2
import bcrypt
import jwt
import db
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

JWT_SECRET = os.getenv('JWT_SECRET')
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required. Set it in .env file.")
if len(JWT_SECRET) < 32:
    raise RuntimeError("JWT_SECRET must be at least 32 characters long. Generate one with: openssl rand -hex 32")
JWT_ALGORITHM = 'HS256'
TOKEN_EXPIRY_HOURS = int(os.getenv('TOKEN_EXPIRY_HOURS', '24'))

# Cookie security: disable secure flag for local HTTP dev by setting COOKIE_SECURE=false
COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'true').lower() in ('1', 'true', 'yes')
COOKIE_SAMESITE = os.getenv('COOKIE_SAMESITE', 'lax')

from courses import courses, get_course, course_levels, conversation_scenarios
from engine import build_system_prompt, detect_mode, find_lesson_context, LEVEL_NAMES
from engine.exercises import check_answer
from engine.flashcards import create_flashcard, review_flashcard, get_due_cards, get_review_stats
from engine.practice import generate_vocab_quiz, generate_conj_quiz, generate_fill_blank_vocab, categorize_vocabulary, get_word_of_day
from engine.adaptive import analyze_weak_areas, get_difficulty_adjustments, build_adaptive_prompt_addition
from engine.content_ingestion import process_french_content
from engine.writing import build_writing_correction_prompt, parse_correction_response, format_correction_for_display
from mock_tests import mock_tests, get_test
from mock_tests.data import get_practice_set_questions, get_section_sets, get_all_section_sets, PRACTICE_SETS_COUNT

def build_limiter(redis_url: str | None = None) -> Limiter:
    """Create a rate limiter. Use Redis storage when a URL is provided."""
    if redis_url:
        return Limiter(key_func=get_remote_address, storage_uri=redis_url)
    return Limiter(key_func=get_remote_address)


REDIS_URL = os.getenv("REDIS_URL")
limiter = build_limiter(REDIS_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and graceful shutdown."""
    logger.info("Starting Parlez server")
    yield
    logger.info("Shutting down Parlez server")
    try:
        storage.close()
    except Exception as exc:
        logger.exception("Error closing storage during shutdown: %s", exc)


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.middleware("http")
async def log_requests_middleware(request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 2)
        logger.info(
            "method=%s path=%s status=%s duration_ms=%s",
            request.method, request.url.path, response.status_code, duration,
        )
        return response
    except Exception as exc:
        duration = round((time.time() - start) * 1000, 2)
        logger.exception(
            "method=%s path=%s duration_ms=%s error=%s",
            request.method, request.url.path, duration, exc,
        )
        raise

@app.middleware("http")
async def no_cache_middleware(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/static/", "/")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"

MAX_CHUNK_LENGTH = 190
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_UPLOAD_TYPES = {"application/pdf", "text/plain", "text/markdown"}
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".txt", ".md"}
MAX_CHAT_MESSAGE_LENGTH = 4000
MAX_WRITING_TEXT_LENGTH = 4000


def validate_user_text(text: str, max_length: int, field_name: str = "text") -> str:
    """Validate and sanitize free-form user text before AI processing."""
    if not isinstance(text, str):
        raise HTTPException(status_code=400, detail=f"{field_name} must be a string")
    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail=f"{field_name} cannot be empty")
    if len(text) > max_length:
        raise HTTPException(status_code=400, detail=f"{field_name} must be at most {max_length} characters")
    return text

def split_text_into_chunks(text):
    if len(text) <= MAX_CHUNK_LENGTH:
        return [text]
    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= MAX_CHUNK_LENGTH:
            chunks.append(remaining)
            break
        split_at = remaining.rfind('.', 0, MAX_CHUNK_LENGTH)
        if split_at < MAX_CHUNK_LENGTH * 0.5:
            split_at = remaining.rfind('!', 0, MAX_CHUNK_LENGTH)
        if split_at < MAX_CHUNK_LENGTH * 0.5:
            split_at = remaining.rfind('?', 0, MAX_CHUNK_LENGTH)
        if split_at < MAX_CHUNK_LENGTH * 0.5:
            split_at = remaining.rfind(' ', 0, MAX_CHUNK_LENGTH)
        if split_at < MAX_CHUNK_LENGTH * 0.3:
            split_at = MAX_CHUNK_LENGTH
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].lstrip()
    return chunks


class ChatMessage(BaseModel):
    message: str
    conv_id: Optional[str] = None
    level: Optional[str] = None
    mode: Optional[str] = None
    scenario_id: Optional[str] = None
    lesson_id: Optional[str] = None

class ConversationCreate(BaseModel):
    title: Optional[str] = None
    level: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    lang: str = "fr"

class ExerciseCheck(BaseModel):
    exercise_id: str
    answer: str
    exercise_data: Optional[dict] = None

class FlashcardReview(BaseModel):
    quality: int  # 1-5

class FlashcardCreate(BaseModel):
    front: str
    back: str
    card_type: str = "vocab"
    level: Optional[str] = None
    lesson_id: Optional[str] = None
    meta: Optional[dict] = None

class VocabQuizRequest(BaseModel):
    level: str = "A1"
    lesson_id: Optional[str] = None
    count: int = 5

class UserSettings(BaseModel):
    level: Optional[str] = "A1"
    name: Optional[str] = None

class SignupRequest(BaseModel):
    username: str
    password: str
    name: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str


# SQLite-backed storage. See db.py for the implementation.
storage = db.Storage()

def create_token(user_id):
    """Create a JWT token for a user."""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        'user_id': user_id,
        'exp': now + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS),
        'iat': now
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token):
    """Verify a JWT token and return user_id."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get('user_id')
    except jwt.PyJWTError:
        return None

def get_current_user(request: Request):
    """Extract user from Authorization header or cookie."""
    # Try Authorization header first
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth[7:]
        user_id = verify_token(token)
        if user_id:
            return storage.get_user_by_id(user_id)
    
    # Try cookie
    token = request.cookies.get('token')
    if token:
        user_id = verify_token(token)
        if user_id:
            return storage.get_user_by_id(user_id)
    
    return None

def require_auth(request: Request):
    """Dependency that requires authentication."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

class RAGKnowledgeBase:
    def __init__(self):
        self.chunks = []
        self.doc_files = []
    
    def add(self, filename, content):
        for i in range(0, len(content), 500):
            chunk = content[i:i+500]
            if chunk.strip():
                self.chunks.append({"text": chunk, "filename": filename})
        if filename not in self.doc_files:
            self.doc_files.append(filename)
    
    def search(self, query, n=5):
        if not self.chunks: return []
        query_lower = query.lower()
        scored = [(c, sum(1 for w in query_lower.split() if w in c["text"].lower())) for c in self.chunks]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c["text"] for c, s in scored[:n] if s > 0]
    
    def count(self): return len(self.chunks)
    def filenames(self): return self.doc_files.copy()

kb = RAGKnowledgeBase()


async def call_nvidia(messages, max_tokens=8192):
    """Call NVIDIA NIM with retries and graceful degradation."""
    if not NVIDIA_API_KEY:
        raise HTTPException(status_code=503, detail="AI service is not configured.")

    async with httpx.AsyncClient(timeout=60.0) as client:
        last_error = None
        for attempt in range(3):
            try:
                r = await client.post(
                    INVOKE_URL,
                    headers={"Authorization": f"Bearer {NVIDIA_API_KEY}", "Content-Type": "application/json"},
                    json={"model": MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.6, "top_p": 0.95}
                )
                if r.status_code == 200:
                    return r.json()
                if r.status_code >= 500:
                    # Retry on server-side errors
                    last_error = f"NVIDIA API error {r.status_code}: {r.text}"
                    logger.warning("NVIDIA API attempt %s failed: %s", attempt + 1, last_error)
                else:
                    # Don't retry client errors (e.g., 400, 401)
                    raise HTTPException(status_code=502, detail=f"AI request failed: {r.status_code}")
            except httpx.RequestError as exc:
                last_error = str(exc)
                logger.warning("NVIDIA API request attempt %s failed: %s", attempt + 1, last_error)

            if attempt < 2:
                await asyncio.sleep(2 ** attempt)

        logger.error("NVIDIA API failed after 3 attempts: %s", last_error)
        raise HTTPException(status_code=503, detail="AI service is temporarily unavailable. Please try again in a moment.")


# ============================================================
# ROUTES
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    html = open("static/landing.html").read()
    return Response(content=html, media_type="text/html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    html = open("static/index.html").read()
    return Response(content=html, media_type="text/html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/health")
async def health():
    """Public health check including database connectivity."""
    db_ok = False
    try:
        with storage.engine.connect() as conn:
            conn.execute(db.text("SELECT 1"))
            db_ok = True
    except Exception as exc:
        logger.error("Health check database connection failed: %s", exc)

    status = 200 if db_ok else 503
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "ok" if db_ok else "error",
    }


# ============================================================
# Authentication
# ============================================================

@app.post("/api/auth/signup")
@limiter.limit("5/minute")
async def signup(request: Request, req: SignupRequest, response: Response):
    """Create a new user account."""
    # Validate username
    if len(req.username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(req.username) > 20:
        raise HTTPException(400, "Username must be at most 20 characters")
    if not req.username.isalnum():
        raise HTTPException(400, "Username must be alphanumeric")
    
    # Check if username exists
    if storage.username_exists(req.username):
        raise HTTPException(400, "Username already taken")
    
    # Validate password
    if len(req.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    
    # Hash password
    password_hash = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create user
    user = storage.create_user(req.username, password_hash, req.name)
    
    # Generate token
    token = create_token(user['id'])
    
    # Set cookie
    response.set_cookie(
        key='token',
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=TOKEN_EXPIRY_HOURS * 3600
    )

    return {
        "token": token,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "name": user['name'],
            "level": user['level']
        }
    }

@app.post("/api/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, req: LoginRequest, response: Response):
    """Log in an existing user."""
    user_id = storage.verify_user(req.username, req.password)
    if not user_id:
        raise HTTPException(401, "Invalid username or password")
    
    user = storage.get_user_by_id(user_id)
    token = create_token(user_id)
    
    response.set_cookie(
        key='token',
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=TOKEN_EXPIRY_HOURS * 3600
    )

    return {
        "token": token,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "name": user['name'],
            "level": user['level']
        }
    }

@app.post("/api/auth/logout")
@limiter.limit("20/minute")
async def logout(request: Request, response: Response):
    """Log out the current user."""
    response.delete_cookie(key='token')
    return {"ok": True}

@app.get("/api/auth/me")
async def get_me(user=Depends(get_current_user)):
    """Get current user info."""
    if not user:
        raise HTTPException(401, "Not authenticated")
    return {
        "id": user['id'],
        "username": user['username'],
        "name": user['name'],
        "level": user['level']
    }


# --- Course API ---

@app.get("/api/courses")
async def get_courses():
    return course_levels

@app.get("/api/courses/{level}")
async def get_course_detail(level: str):
    course = get_course(level.upper())
    return {
        'level': course.level, 'title': course.title, 'book': course.book,
        'description': course.description, 'cefrDescription': course.cefrDescription,
        'color': course.color,
        'units': [{
            'id': u.id, 'title': u.title, 'titleFr': u.titleFr,
            'theme': u.theme, 'description': u.description,
            'lessons': [{
                'id': l.id, 'title': l.title, 'titleFr': l.titleFr,
                'description': l.description, 'objectives': l.objectives,
                'estimatedMinutes': l.estimatedMinutes,
                'hasVocabulary': bool(l.vocabulary),
                'hasGrammar': bool(l.grammar),
                'hasConjugation': l.conjugation is not None,
                'hasDialogue': bool(l.dialogue),
                'exerciseCount': len(l.exercises),
            } for l in u.lessons]
        } for u in course.units]
    }

@app.get("/api/courses/{level}/lessons/{lesson_id}")
async def get_lesson(level: str, lesson_id: str):
    course = get_course(level.upper())
    for unit in course.units:
        for lesson in unit.lessons:
            if lesson.id == lesson_id:
                return {
                    'id': lesson.id, 'title': lesson.title, 'titleFr': lesson.titleFr,
                    'description': lesson.description, 'objectives': lesson.objectives,
                    'vocabulary': [{'fr': v.fr, 'en': v.en, 'ipa': v.ipa, 'example': v.example, 'exampleEn': v.exampleEn, 'category': v.category} for v in lesson.vocabulary],
                    'grammar': [{'title': g.title, 'explanation': g.explanation, 'examples': [{'fr': e.fr, 'en': e.en} for e in g.examples], 'table': {'headers': g.table.headers, 'rows': g.table.rows, 'caption': g.table.caption} if g.table else None, 'tip': g.tip} for g in lesson.grammar],
                    'conjugation': {
                        'verbs': [{'infinitive': v.infinitive, 'translation': v.translation, 'tense': v.tense, 'conjugations': v.conjugations, 'sentenceRule': v.sentenceRule, 'sentenceExamples': [{'fr': e.fr, 'en': e.en} for e in v.sentenceExamples]} for v in lesson.conjugation.verbs],
                        'practice': [{'id': e.id, 'type': e.type, 'prompt': e.prompt, 'promptFr': e.promptFr, 'options': e.options, 'answer': e.answer, 'explanation': e.explanation} for e in lesson.conjugation.practice],
                    } if lesson.conjugation else None,
                    'dialogue': [{'speaker': d.speaker, 'name': d.name, 'fr': d.fr, 'en': d.en} for d in lesson.dialogue],
                    'exercises': [{'id': e.id, 'type': e.type, 'prompt': e.prompt, 'promptFr': e.promptFr, 'options': e.options, 'answer': e.answer, 'explanation': e.explanation, 'pairs': e.pairs, 'wordBank': e.wordBank, 'words': e.words, 'audioText': e.audioText} for e in lesson.exercises],
                    'activities': [{'id': e.id, 'type': e.type, 'prompt': e.prompt, 'options': e.options, 'answer': e.answer, 'explanation': e.explanation, 'wordBank': e.wordBank, 'words': e.words, 'audioText': e.audioText} for e in lesson.activities],
                    'culturalNote': lesson.culturalNote,
                    'estimatedMinutes': lesson.estimatedMinutes,
                }
    raise HTTPException(404, "Lesson not found")


@app.get("/api/scenarios")
async def get_scenarios():
    return [{'id': s.id, 'label': s.label, 'labelFr': s.labelFr, 'description': s.description, 'icon': s.icon} for s in conversation_scenarios]


# --- User Settings ---

@app.get("/api/user")
async def get_user(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    return {"level": user.get('level', 'A1'), "name": user.get('name', ''), "username": user.get('username', '')}

@app.post("/api/user")
async def update_user(settings: UserSettings, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    if settings.level: user['level'] = settings.level.upper()
    if settings.name: user['name'] = settings.name
    storage.save_user(user)
    return {"level": user.get('level', 'A1'), "name": user.get('name', ''), "username": user.get('username', '')}


# --- Conversations ---

@app.get("/api/conversations")
async def get_conversations(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    convs = user.get('conversations', {})
    return sorted(convs.values(), key=lambda x: x.get("updated", 0), reverse=True)

@app.post("/api/conversations")
async def create_conversation(conv: ConversationCreate, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    conv_id = str(uuid.uuid4())[:8]
    level = conv.level or user.get('level', 'A1')
    user.setdefault('conversations', {})[conv_id] = {
        "id": conv_id, "title": conv.title or "New Chat",
        "level": level, "messages": [],
        "created": time.time(), "updated": time.time()
    }
    storage.save_user(user)
    return user['conversations'][conv_id]

@app.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    conv = user.get('conversations', {}).get(conv_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return conv

@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    convs = user.get('conversations', {})
    if conv_id not in convs:
        raise HTTPException(404, "Conversation not found")
    del convs[conv_id]
    storage.save_user(user)
    return {"ok": True}


# --- Chat ---

@app.post("/api/chat")
@limiter.limit("30/minute")
async def chat(request: Request, msg: ChatMessage, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    
    message = validate_user_text(msg.message, MAX_CHAT_MESSAGE_LENGTH, "message")
    
    level = msg.level or user.get('level', 'A1')
    
    # Detect mode from message
    mode = msg.mode or detect_mode(message, level)
    
    # Find lesson context if needed
    lesson_ctx = None
    if msg.lesson_id:
        for course in courses:
            for unit in course.units:
                for lesson in unit.lessons:
                    if lesson.id == msg.lesson_id:
                        lesson_ctx = {
                            'id': lesson.id, 'title': lesson.title, 'titleFr': lesson.titleFr,
                            'description': lesson.description, 'objectives': lesson.objectives,
                            'vocabulary': [{'fr': v.fr, 'en': v.en, 'ipa': v.ipa, 'example': v.example} for v in lesson.vocabulary] if lesson.vocabulary else [],
                            'grammar': [{'title': g.title, 'explanation': g.explanation, 'examples': [{'fr': e.fr, 'en': e.en} for e in g.examples]} for g in lesson.grammar] if lesson.grammar else [],
                            'dialogue': [{'speaker': d.speaker, 'name': d.name, 'fr': d.fr, 'en': d.en} for d in lesson.dialogue] if lesson.dialogue else [],
                            'culturalNote': lesson.culturalNote,
                        }
                        break
    elif mode == 'lesson':
        lesson_ctx = find_lesson_context(message, courses)
    
    # Find scenario if in conversation mode
    scenario = None
    if msg.scenario_id:
        for s in conversation_scenarios:
            if s.id == msg.scenario_id:
                scenario = {'name': s.label, 'description': s.description}
                break
    
    # Get weak areas for personalized teaching
    user_history = user.get('exercise_history', [])
    user_test_results = user.get('test_results', [])
    weak_analysis = analyze_weak_areas(user_history, user_test_results)
    adjustments = get_difficulty_adjustments(level, weak_analysis)
    
    # Build system prompt
    system_prompt = build_system_prompt(level=level, mode=mode, lesson_context=lesson_ctx, scenario=scenario)
    system_prompt += build_adaptive_prompt_addition(level, weak_analysis, adjustments)
    
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    conv = user.get('conversations', {}).get(msg.conv_id, {})
    for m in conv.get("messages", [])[-15:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": message})
    
    # Call AI
    try:
        r = await call_nvidia(messages)
        resp = r["choices"][0]["message"]["content"]
    except Exception as e:
        resp = f"I apologize, but I encountered an error: {str(e)}. Please try again."
    
    # Save to conversation
    user_convs = user.get('conversations', {})
    if msg.conv_id and msg.conv_id in user_convs:
        user_convs[msg.conv_id]["messages"].append({"role": "user", "content": message})
        user_convs[msg.conv_id]["messages"].append({"role": "assistant", "content": resp})
        user_convs[msg.conv_id]["updated"] = time.time()
        if not user_convs[msg.conv_id].get("title_set"):
            user_convs[msg.conv_id]["title"] = message[:50]
        storage.save_user(user)
    
    # Update XP
    progress = user.setdefault('progress', {"xp": 0, "streak": 0, "best_streak": 0, "last_active": None})
    progress['xp'] = progress.get('xp', 0) + 5
    today = datetime.date.today().isoformat()
    last = progress.get('last_active')
    if last == today:
        pass
    elif last == str(datetime.date.today() - datetime.timedelta(days=1)):
        progress['streak'] = progress.get('streak', 0) + 1
        progress['best_streak'] = max(progress.get('best_streak', 0), progress['streak'])
    else:
        progress['streak'] = 1
    progress['last_active'] = today
    storage.save_user(user)
    
    return {
        "response": resp,
        "mode": mode,
        "level": level,
        "xp_earned": 5,
        "total_xp": progress.get('xp', 0),
    }


# --- Exercise checking ---

@app.post("/api/check-exercise")
async def check_exercise(req: ExerciseCheck, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    
    exercise = req.exercise_data or {}
    is_correct, explanation = check_answer(exercise, req.answer)
    
    progress = user.setdefault('progress', {"xp": 0})
    if is_correct:
        progress['xp'] = progress.get('xp', 0) + 10
    
    # Track exercise history
    history_entry = {
        'exercise_id': req.exercise_id,
        'type': exercise.get('type', 'unknown'),
        'answer': req.answer,
        'correct': is_correct,
        'explanation': explanation,
        'level': user.get('level', 'A1'),
        'timestamp': time.time(),
    }
    user.setdefault('exercise_history', []).append(history_entry)
    
    # Keep only last 500 entries
    if len(user['exercise_history']) > 500:
        user['exercise_history'] = user['exercise_history'][-500:]
    
    storage.save_user(user)
    
    return {
        "correct": is_correct,
        "explanation": explanation,
        "xp_earned": 10 if is_correct else 0,
        "total_xp": progress.get('xp', 0),
    }


# --- Exercise History ---

@app.get("/api/exercise-history")
async def get_exercise_history(limit: int = 50, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user.get('exercise_history', [])[-limit:]

@app.get("/api/exercise-stats")
async def get_exercise_stats(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    history = user.get('exercise_history', [])
    if not history:
        return {"total": 0, "correct": 0, "accuracy": 0, "by_type": {}, "weak_areas": []}
    
    total = len(history)
    correct = sum(1 for h in history if h.get('correct'))
    
    # Stats by exercise type
    by_type = {}
    for h in history:
        t = h.get('type', 'unknown')
        if t not in by_type:
            by_type[t] = {'total': 0, 'correct': 0}
        by_type[t]['total'] += 1
        if h.get('correct'):
            by_type[t]['correct'] += 1
    
    # Calculate accuracy by type and identify weak areas
    weak_areas = []
    for t, stats in by_type.items():
        accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        stats['accuracy'] = round(accuracy)
        if accuracy < 60 and stats['total'] >= 3:
            weak_areas.append({'type': t, 'accuracy': round(accuracy), 'total': stats['total']})
    
    weak_areas.sort(key=lambda x: x['accuracy'])
    
    return {
        "total": total,
        "correct": correct,
        "accuracy": round((correct / total) * 100) if total > 0 else 0,
        "by_type": by_type,
        "weak_areas": weak_areas,
        "recent_accuracy": round((correct / total) * 100) if total > 0 else 0,
    }


# --- Progress ---

@app.get("/api/progress")
async def get_progress(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user.get('progress', {})

@app.post("/api/progress/complete-lesson")
async def complete_lesson(data: dict, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    lesson_id = data.get('lesson_id')
    score = data.get('score', 0)
    progress = user.setdefault('progress', {})
    if lesson_id and lesson_id not in progress.get('lessons_completed', []):
        progress.setdefault('lessons_completed', []).append(lesson_id)
        progress['xp'] = progress.get('xp', 0) + 50
    storage.save_user(user)
    return progress

@app.get("/api/streaks")
async def get_streaks(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    progress = user.get('progress', {})
    today = datetime.date.today().isoformat()
    last = progress.get("last_active")
    current = progress.get("streak", 0)
    if last == today:
        return {"current": current, "best": progress.get("best_streak", 0)}
    elif last == str(datetime.date.today() - datetime.timedelta(days=1)):
        current += 1
        progress["streak"] = current
        progress["best_streak"] = max(progress.get("best_streak", 0), current)
    else:
        progress["streak"] = 1
    progress["last_active"] = today
    storage.save_user(user)
    return {"current": progress.get("streak", 1), "best": progress.get("best_streak", 1)}


# --- Flashcards ---

@app.get("/api/flashcards")
async def get_all_flashcards(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    return list(user.get('flashcards', {}).values())

@app.get("/api/flashcards/due")
async def get_due_flashcards(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    cards = list(user.get('flashcards', {}).values())
    return get_due_cards(cards)

@app.get("/api/flashcards/stats")
async def get_flashcard_stats(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    cards = list(user.get('flashcards', {}).values())
    return get_review_stats(cards)

@app.post("/api/flashcards")
async def create_flashcard_endpoint(req: FlashcardCreate, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    card = create_flashcard(
        front=req.front, back=req.back, card_type=req.card_type,
        level=req.level or user.get('level', 'A1'),
        lesson_id=req.lesson_id, meta=req.meta
    )
    user.setdefault('flashcards', {})[card['id']] = card
    storage.save_user(user)
    return card

@app.post("/api/flashcards/bulk")
async def create_bulk_flashcards(cards: list[FlashcardCreate], user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    created = []
    user_flashcards = user.setdefault('flashcards', {})
    for req in cards:
        card = create_flashcard(
            front=req.front, back=req.back, card_type=req.card_type,
            level=req.level or user.get('level', 'A1'),
            lesson_id=req.lesson_id, meta=req.meta
        )
        user_flashcards[card['id']] = card
        created.append(card)
    storage.save_user(user)
    return {"created": len(created), "cards": created}

@app.post("/api/flashcards/{card_id}/review")
async def review_flashcard_endpoint(card_id: str, req: FlashcardReview, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    user_flashcards = user.get('flashcards', {})
    if card_id not in user_flashcards:
        raise HTTPException(404, "Card not found")
    card = review_flashcard(user_flashcards[card_id], req.quality)
    user_flashcards[card_id] = card
    progress = user.setdefault('progress', {"xp": 0})
    progress['xp'] = progress.get('xp', 0) + 5
    storage.save_user(user)
    return {"card": card, "xp_earned": 5, "total_xp": progress.get('xp', 0)}

@app.delete("/api/flashcards/{card_id}")
async def delete_flashcard(card_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    user_flashcards = user.get('flashcards', {})
    if card_id in user_flashcards:
        del user_flashcards[card_id]
        storage.save_user(user)
    return {"ok": True}

@app.delete("/api/flashcards")
async def clear_flashcards(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    user['flashcards'] = {}
    storage.save_user(user)
    return {"ok": True}


# --- Vocabulary Practice ---

@app.post("/api/practice/lesson/{level}/{lesson_id}")
async def lesson_practice(level: str, lesson_id: str):
    """Generate a full practice set from a lesson's exercises."""
    course = get_course(level.upper())
    for unit in course.units:
        for lesson in unit.lessons:
            if lesson.id == lesson_id:
                exercises = []
                # Add lesson exercises
                for e in lesson.exercises:
                    ex = {'id': e.id, 'type': e.type, 'prompt': e.prompt, 'promptFr': e.promptFr,
                          'options': e.options, 'answer': e.answer, 'acceptable': e.acceptable,
                          'explanation': e.explanation, 'pairs': e.pairs, 'wordBank': e.wordBank,
                          'words': e.words, 'audioText': e.audioText, 'hint': e.hint}
                    exercises.append(ex)
                # Add activities
                for e in lesson.activities:
                    ex = {'id': e.id, 'type': e.type, 'prompt': e.prompt,
                          'options': e.options, 'answer': e.answer, 'acceptable': e.acceptable,
                          'explanation': e.explanation, 'wordBank': e.wordBank,
                          'words': e.words, 'audioText': e.audioText}
                    exercises.append(ex)
                # Add conjugation practice
                if lesson.conjugation and lesson.conjugation.practice:
                    for e in lesson.conjugation.practice:
                        ex = {'id': e.id, 'type': e.type, 'prompt': e.prompt, 'promptFr': e.promptFr,
                              'options': e.options, 'answer': e.answer, 'acceptable': e.acceptable,
                              'explanation': e.explanation}
                        exercises.append(ex)
                
                return {
                    'lesson': {'id': lesson.id, 'title': lesson.title, 'titleFr': lesson.titleFr},
                    'exercises': exercises,
                    'total': len(exercises),
                }
    raise HTTPException(404, "Lesson not found")


@app.post("/api/practice/vocab-quiz")
async def vocab_quiz(req: VocabQuizRequest):
    """Generate a vocabulary quiz from course data."""
    course = get_course(req.level)
    all_vocab = []
    
    if req.lesson_id:
        for unit in course.units:
            for lesson in unit.lessons:
                if lesson.id == req.lesson_id and lesson.vocabulary:
                    all_vocab.extend([{'fr': v.fr, 'en': v.en, 'ipa': v.ipa, 'example': v.example, 'exampleEn': v.exampleEn, 'category': v.category} for v in lesson.vocabulary])
    else:
        for unit in course.units:
            for lesson in unit.lessons:
                if lesson.vocabulary:
                    all_vocab.extend([{'fr': v.fr, 'en': v.en, 'ipa': v.ipa, 'example': v.example, 'exampleEn': v.exampleEn, 'category': v.category} for v in lesson.vocabulary])
    
    if not all_vocab:
        # Generate from AI if no course data
        return {"quiz": None, "message": "No vocabulary data available for this level yet. Ask the AI to teach you vocabulary!"}
    
    quiz = generate_vocab_quiz(all_vocab, n=req.count)
    return {"quiz": quiz}

@app.post("/api/practice/conj-quiz")
async def conj_quiz(req: VocabQuizRequest):
    """Generate a conjugation quiz from course data."""
    course = get_course(req.level)
    all_conj = None
    
    if req.lesson_id:
        for unit in course.units:
            for lesson in unit.lessons:
                if lesson.id == req.lesson_id and lesson.conjugation:
                    all_conj = {
                        'verbs': [{'infinitive': v.infinitive, 'translation': v.translation, 'tense': v.tense, 'conjugations': v.conjugations} for v in lesson.conjugation.verbs]
                    }
                    break
    else:
        for unit in course.units:
            for lesson in unit.lessons:
                if lesson.conjugation:
                    all_conj = {
                        'verbs': [{'infinitive': v.infinitive, 'translation': v.translation, 'tense': v.tense, 'conjugations': v.conjugations} for v in lesson.conjugation.verbs]
                    }
                    break
        if not all_conj:
            for unit in course.units:
                for lesson in unit.lessons:
                    if lesson.conjugation:
                        if not all_conj:
                            all_conj = {'verbs': []}
                        all_conj['verbs'].extend([{'infinitive': v.infinitive, 'translation': v.translation, 'tense': v.tense, 'conjugations': v.conjugations} for v in lesson.conjugation.verbs])
    
    if not all_conj or not all_conj.get('verbs'):
        return {"quiz": None, "message": "No conjugation data available. Ask the AI to teach you verb conjugation!"}
    
    quiz = generate_conj_quiz(all_conj, n=req.count)
    return {"quiz": quiz}

@app.post("/api/practice/fill-blank")
async def fill_blank_practice(req: VocabQuizRequest):
    """Generate fill-in-the-blank vocabulary exercises."""
    course = get_course(req.level)
    all_vocab = []
    
    for unit in course.units:
        for lesson in unit.lessons:
            if req.lesson_id and lesson.id != req.lesson_id:
                continue
            if lesson.vocabulary:
                all_vocab.extend([{'fr': v.fr, 'en': v.en, 'ipa': v.ipa} for v in lesson.vocabulary])
    
    if not all_vocab:
        return {"exercises": [], "message": "No vocabulary data available."}
    
    exercises = generate_fill_blank_vocab(all_vocab, n=req.count)
    return {"exercises": exercises}

@app.get("/api/mock-tests")
async def get_mock_tests():
    """List available mock tests."""
    return [{'type': t.type, 'name': t.name, 'fullName': t.fullName, 'description': t.description,
             'administeredBy': t.administeredBy, 'usedFor': t.usedFor, 'color': t.color,
             'sections': [{'id': s.id, 'title': s.title, 'titleFr': s.titleFr, 'description': s.description,
                           'icon': s.icon, 'questionCount': s.questionCount, 'durationMinutes': s.durationMinutes}
                          for s in t.sections]} for t in mock_tests]

@app.get("/api/mock-tests/{test_type}")
async def get_mock_test(test_type: str):
    """Get a mock test with all questions."""
    test = get_test(test_type)
    return {
        'type': test.type, 'name': test.name, 'fullName': test.fullName,
        'description': test.description, 'color': test.color,
        'sections': [{
            'id': s.id, 'title': s.title, 'titleFr': s.titleFr,
            'description': s.description, 'icon': s.icon,
            'questionCount': s.questionCount, 'durationMinutes': s.durationMinutes,
            'questions': [{'id': q.id, 'type': q.type, 'prompt': q.prompt, 'promptFr': q.promptFr,
                           'options': q.options, 'answer': q.answer, 'explanation': q.explanation,
                           'audioText': q.audioText, 'level': q.level} for q in s.questions]
        } for s in test.sections]
    }

@app.get("/api/mock-tests/{test_type}/sections/{section_id}")
async def get_test_section(test_type: str, section_id: str):
    """Get a specific test section with questions."""
    test = get_test(test_type)
    for s in test.sections:
        if s.id == section_id:
            return {
                'id': s.id, 'title': s.title, 'titleFr': s.titleFr,
                'description': s.description, 'icon': s.icon,
                'questionCount': s.questionCount, 'durationMinutes': s.durationMinutes,
                'questions': [{'id': q.id, 'type': q.type, 'prompt': q.prompt, 'promptFr': q.promptFr,
                               'options': q.options, 'answer': q.answer, 'explanation': q.explanation,
                               'audioText': q.audioText, 'level': q.level} for q in s.questions]
            }
    raise HTTPException(404, "Section not found")

@app.post("/api/mock-tests/{test_type}/submit")
async def submit_test(test_type: str, data: dict, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    """Submit test answers and get results."""
    answers = data.get('answers', {})  # {question_id: selected_index}
    section_id = data.get('section_id')
    duration_sec = data.get('duration_sec', 0)
    
    test = get_test(test_type)
    correct = 0
    total = 0
    details = []
    
    for s in test.sections:
        if section_id and s.id != section_id:
            continue
        for q in s.questions:
            total += 1
            user_answer = answers.get(q.id)
            is_correct = user_answer == q.answer
            if is_correct:
                correct += 1
            details.append({
                'question_id': q.id, 'correct': is_correct,
                'user_answer': user_answer, 'correct_answer': q.answer,
                'explanation': q.explanation
            })
    
    score = round((correct / total) * 100) if total > 0 else 0
    
    # Estimate level based on score
    level = 'A1'
    if score >= 90: level = 'C1'
    elif score >= 80: level = 'B2'
    elif score >= 65: level = 'B1'
    elif score >= 50: level = 'A2'
    
    result = {
        'testType': test_type, 'section': section_id or 'all',
        'score': score, 'correct': correct, 'total': total,
        'durationSec': duration_sec, 'level': level,
        'takenAt': datetime.datetime.now().isoformat(),
        'details': details,
    }
    
    user.setdefault('test_results', []).append(result)
    progress = user.setdefault('progress', {"xp": 0})
    progress['xp'] = progress.get('xp', 0) + (correct * 5)
    storage.save_user(user)
    
    return result

@app.get("/api/test-results")
async def get_test_results(limit: int = 20, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user.get('test_results', [])[-limit:]

@app.get("/api/test-results/stats")
async def get_test_stats(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    results = user.get('test_results', [])
    if not results:
        return {'total': 0, 'by_type': {}, 'avg_score': 0, 'best_scores': {}}
    
    by_type = {}
    for r in results:
        t = r.get('testType', 'unknown')
        if t not in by_type:
            by_type[t] = {'total': 0, 'scores': []}
        by_type[t]['total'] += 1
        by_type[t]['scores'].append(r.get('score', 0))
    
    for t, stats in by_type.items():
        stats['avg_score'] = round(sum(stats['scores']) / len(stats['scores'])) if stats['scores'] else 0
        stats['best_score'] = max(stats['scores']) if stats['scores'] else 0
        del stats['scores']
    
    all_scores = [r.get('score', 0) for r in results]
    
    return {
        'total': len(results),
        'by_type': by_type,
        'avg_score': round(sum(all_scores) / len(all_scores)) if all_scores else 0,
        'best_scores': {t: stats.get('best_score', 0) for t, stats in by_type.items()},
    }


# ============================================================
# Exam Simulation Mode
# ============================================================

@app.get("/api/exam/sets/{test_type}")
async def get_exam_sets(test_type: str):
    """Get all practice sets for a test type."""
    test = get_test(test_type.upper())
    return {
        'type': test.type,
        'name': test.name,
        'fullName': test.fullName,
        'description': test.description,
        'administeredBy': test.administeredBy,
        'usedFor': test.usedFor,
        'color': test.color,
        'sections': get_all_section_sets(test_type),
    }

@app.get("/api/exam/sets/{test_type}/{section_id}")
async def get_section_detail(test_type: str, section_id: str):
    """Get section details with practice set list."""
    test = get_test(test_type.upper())
    for s in test.sections:
        if s.id == section_id:
            return {
                'id': s.id,
                'title': s.title,
                'titleFr': s.titleFr,
                'description': s.description,
                'icon': s.icon,
                'durationMinutes': s.durationMinutes,
                'sets': get_section_sets(test_type, section_id),
            }
    raise HTTPException(404, "Section not found")

@app.get("/api/exam/questions/{test_type}/{section_id}/{set_num}")
@limiter.limit("30/minute")
async def get_exam_questions(request: Request, test_type: str, section_id: str, set_num: int):
    """Get questions for a specific practice set."""
    if set_num < 1 or set_num > PRACTICE_SETS_COUNT:
        raise HTTPException(400, f"Set number must be 1-{PRACTICE_SETS_COUNT}")
    
    questions = get_practice_set_questions(test_type, section_id, set_num)
    if not questions:
        return {"questions": [], "message": "No questions available for this set. Try sets 1-3."}
    
    return {"questions": questions, "total": len(questions)}

@app.post("/api/exam/submit/{test_type}/{section_id}/{set_num}")
@limiter.limit("20/minute")
async def submit_exam(request: Request, test_type: str, section_id: str, set_num: int, data: dict, user=Depends(get_current_user)):
    """Submit exam answers and get results with level estimation."""
    if not user:
        raise HTTPException(401, "Not authenticated")
    
    answers = data.get('answers', {})
    duration_sec = data.get('duration_sec', 0)
    
    questions = get_practice_set_questions(test_type, section_id, set_num)
    if not questions:
        raise HTTPException(400, "No questions for this set")
    
    correct = 0
    total = len(questions)
    details = []
    
    for q in questions:
        user_answer = answers.get(q['id'])
        is_correct = user_answer == q['answer']
        if is_correct:
            correct += 1
        details.append({
            'question_id': q['id'],
            'correct': is_correct,
            'user_answer': user_answer,
            'correct_answer': q['answer'],
            'prompt': q.get('prompt', '')[:100],
            'explanation': q.get('explanation', ''),
            'level': q.get('level', 'A1'),
        })
    
    score = round((correct / total) * 100) if total > 0 else 0
    
    # Level estimation based on score
    level = 'A1'
    if score >= 90: level = 'C1'
    elif score >= 80: level = 'B2'
    elif score >= 65: level = 'B1'
    elif score >= 50: level = 'A2'
    
    # Calculate level breakdown
    level_breakdown = {}
    for d in details:
        lvl = d.get('level', 'A1')
        if lvl not in level_breakdown:
            level_breakdown[lvl] = {'correct': 0, 'total': 0}
        level_breakdown[lvl]['total'] += 1
        if d['correct']:
            level_breakdown[lvl]['correct'] += 1
    
    for lvl in level_breakdown:
        stats = level_breakdown[lvl]
        stats['accuracy'] = round((stats['correct'] / stats['total'] * 100)) if stats['total'] > 0 else 0
    
    result = {
        'testType': test_type,
        'section': section_id,
        'setNum': set_num,
        'score': score,
        'correct': correct,
        'total': total,
        'durationSec': duration_sec,
        'level': level,
        'levelBreakdown': level_breakdown,
        'takenAt': datetime.datetime.now().isoformat(),
        'details': details,
    }
    
    user.setdefault('test_results', []).append(result)
    progress = user.setdefault('progress', {"xp": 0})
    progress['xp'] = progress.get('xp', 0) + (correct * 5)
    storage.save_user(user)
    
    return result

@app.get("/api/exam/history/{test_type}")
async def get_exam_history(test_type: str, user=Depends(get_current_user)):
    """Get test history for a specific test type."""
    if not user:
        raise HTTPException(401, "Not authenticated")
    results = user.get('test_results', [])
    return [r for r in results if r.get('testType') == test_type.upper()]

@app.get("/api/adaptive/analysis")
async def get_adaptive_analysis(user=Depends(get_current_user)):
    """Get adaptive difficulty analysis for the current user."""
    if not user:
        raise HTTPException(401, "Not authenticated")
    
    user_history = user.get('exercise_history', [])
    user_test_results = user.get('test_results', [])
    level = user.get('level', 'A1')
    
    analysis = analyze_weak_areas(user_history, user_test_results)
    adjustments = get_difficulty_adjustments(level, analysis)
    
    return {
        'analysis': analysis,
        'adjustments': adjustments,
        'level': level,
        'levelName': LEVEL_NAMES.get(level, 'A1'),
    }


class ContentIngestRequest(BaseModel):
    text: str
    level: Optional[str] = None

class WritingCorrectionRequest(BaseModel):
    text: str
    level: Optional[str] = None

@app.post("/api/writing/correct")
async def correct_writing(req: WritingCorrectionRequest, user=Depends(get_current_user)):
    """Correct French writing with inline annotations."""
    if not user:
        raise HTTPException(401, "Not authenticated")
    
    text = validate_user_text(req.text, MAX_WRITING_TEXT_LENGTH, "text")
    level = req.level or user.get('level', 'A1')
    system_prompt = build_writing_correction_prompt(text, level)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Please correct this French text:\n\n{text}"}
    ]
    
    try:
        r = await call_nvidia(messages)
        resp = r["choices"][0]["message"]["content"]
    except HTTPException:
        raise
    except Exception:
        logger.exception("Writing correction AI call failed")
        raise HTTPException(status_code=503, detail="AI service is temporarily unavailable. Please try again.")

    # Parse structured correction
    correction = parse_correction_response(resp)
    
    # Format for display
    formatted = format_correction_for_display(correction)
    
    # Track XP for writing practice
    progress = user.setdefault('progress', {"xp": 0})
    progress['xp'] = progress.get('xp', 0) + 15
    storage.save_user(user)
    
    return {
        "response": resp,
        "correction": correction,
        "formatted": formatted,
        "xp_earned": 15,
        "total_xp": progress.get('xp', 0),
    }


@app.post("/api/content/ingest")
async def ingest_content(req: ContentIngestRequest, user=Depends(get_current_user)):
    """Process French text content to extract vocabulary, flashcards, and quizzes."""
    if not user:
        raise HTTPException(401, "Not authenticated")
    
    level = req.level or user.get('level', 'A1')
    result = process_french_content(req.text, level)
    
    # Auto-create flashcards from extracted vocabulary
    if result['flashcards']:
        user_flashcards = user.setdefault('flashcards', {})
        for card_data in result['flashcards']:
            card = create_flashcard(
                front=card_data['front'], back=card_data['back'],
                card_type=card_data['card_type'], level=card_data['level'],
                meta=card_data.get('meta', {})
            )
            user_flashcards[card['id']] = card
        storage.save_user(user)
    
    return {
        'vocabulary': result['vocabulary'],
        'flashcards_count': len(result['flashcards']),
        'quiz': result['quiz'],
        'summary': result['summary'],
    }


@app.get("/api/exam/stats/{test_type}")
async def get_exam_stats(test_type: str, user=Depends(get_current_user)):
    """Get detailed stats for a test type."""
    if not user:
        raise HTTPException(401, "Not authenticated")
    
    results = [r for r in user.get('test_results', []) if r.get('testType') == test_type.upper()]
    
    if not results:
        return {'total': 0, 'avg_score': 0, 'best_score': 0, 'by_section': {}, 'by_level': {}, 'recent': []}
    
    scores = [r.get('score', 0) for r in results]
    
    by_section = {}
    for r in results:
        s = r.get('section', 'unknown')
        if s not in by_section:
            by_section[s] = {'total': 0, 'scores': []}
        by_section[s]['total'] += 1
        by_section[s]['scores'].append(r.get('score', 0))
    
    for s, stats in by_section.items():
        stats['avg_score'] = round(sum(stats['scores']) / len(stats['scores'])) if stats['scores'] else 0
        stats['best_score'] = max(stats['scores']) if stats['scores'] else 0
        del stats['scores']
    
    by_level = {}
    for r in results:
        for lvl, stats in r.get('levelBreakdown', {}).items():
            if lvl not in by_level:
                by_level[lvl] = {'correct': 0, 'total': 0}
            by_level[lvl]['correct'] += stats.get('correct', 0)
            by_level[lvl]['total'] += stats.get('total', 0)
    
    for lvl in by_level:
        s = by_level[lvl]
        s['accuracy'] = round((s['correct'] / s['total'] * 100)) if s['total'] > 0 else 0
    
    return {
        'total': len(results),
        'avg_score': round(sum(scores) / len(scores)),
        'best_score': max(scores),
        'by_section': by_section,
        'by_level': by_level,
        'recent': results[-5:],
    }


@app.get("/api/practice/word-of-day")
async def word_of_day(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    course = get_course(user.get('level', 'A1'))
    all_vocab = []
    for unit in course.units:
        for lesson in unit.lessons:
            if lesson.vocabulary:
                all_vocab.extend([{'fr': v.fr, 'en': v.en, 'ipa': v.ipa, 'example': v.example, 'exampleEn': v.exampleEn} for v in lesson.vocabulary])
    
    word = get_word_of_day(all_vocab)
    return {"word": word, "level": user.get('level', 'A1')}

@app.get("/api/practice/vocab-categories")
async def vocab_categories(level: str = "A1"):
    """Get vocabulary grouped by category."""
    course = get_course(level)
    all_vocab = []
    for unit in course.units:
        for lesson in unit.lessons:
            if lesson.vocabulary:
                all_vocab.extend([{'fr': v.fr, 'en': v.en, 'ipa': v.ipa, 'example': v.example, 'category': v.category} for v in lesson.vocabulary])
    
    categories = categorize_vocabulary(all_vocab)
    return {cat: words for cat, words in categories.items()}


# ============================================================
# Phase 4: Collaboration — Comments, Share, Export
# ============================================================

class CommentCreate(BaseModel):
    conv_id: str
    message: str
    author: str = "You"

class CommentDelete(BaseModel):
    conv_id: str
    comment_id: str

class ShareCreate(BaseModel):
    conv_id: str

class ExportRequest(BaseModel):
    conv_id: str
    format: str = "markdown"  # "markdown" or "json"

@app.post("/api/comments")
async def add_comment(req: CommentCreate, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")

    comment = {
        "id": str(uuid.uuid4())[:8],
        "message": req.message,
        "author": user.get('name', user.get('username', 'User')),
        "user_id": user['id'],
        "created_at": time.time()
    }
    storage.add_comment(req.conv_id, comment)
    return comment

@app.get("/api/comments/{conv_id}")
async def get_comments(conv_id: str, user=Depends(require_auth)):
    return storage.get_comments(conv_id)

@app.delete("/api/comments/{conv_id}/{comment_id}")
async def delete_comment(conv_id: str, comment_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    storage.delete_comment(conv_id, comment_id)
    return {"ok": True}

@app.post("/api/share")
async def create_share(req: ShareCreate, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    user_convs = user.get('conversations', {})
    if req.conv_id not in user_convs:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = user_convs[req.conv_id]
    share_id = str(uuid.uuid4())[:8]

    data = {
        "id": share_id,
        "conv_id": req.conv_id,
        "user_id": user['id'],
        "title": conv.get("title", "Shared Chat"),
        "messages": conv.get("messages", []),
        "created_at": time.time(),
        "include_files": True,
        "format": "markdown"
    }
    storage.create_shared(share_id, data)

    return {
        "share_id": share_id,
        "url": f"/share/{share_id}",
        "title": conv.get("title", "Shared Chat")
    }

@app.get("/api/share/{share_id}")
async def get_shared(share_id: str):
    shared = storage.get_shared(share_id)
    if not shared:
        raise HTTPException(status_code=404, detail="Shared conversation not found")
    return shared

@app.get("/api/shared")
async def list_shared(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    return storage.list_shared_by_user(user['id'])

@app.delete("/api/share/{share_id}")
async def delete_share(share_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    storage.delete_shared(share_id)
    return {"ok": True}

@app.post("/api/export")
async def export_conversation(req: ExportRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    user_convs = user.get('conversations', {})
    if req.conv_id not in user_convs:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv = user_convs[req.conv_id]
    messages = conv.get("messages", [])
    title = conv.get("title", "Chat")
    level = conv.get("level", "A1")
    created = conv.get("created_at", time.time())
    
    if req.format == "json":
        return {
            "format": "json",
            "title": title,
            "level": level,
            "created_at": created,
            "messages": messages,
            "comments": storage.get_comments(req.conv_id)
        }
    
    # Markdown format
    md_lines = [
        f"# {title}",
        "",
        f"**Level:** {level} | **Created:** {datetime.datetime.fromtimestamp(created).strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        ""
    ]
    
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", 0)
        time_str = datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M') if timestamp else ""
        
        if role == "user":
            md_lines.append(f"### 👤 You {f'({time_str})' if time_str else ''}")
        else:
            md_lines.append(f"### 🤖 Parlez {f'({time_str})' if time_str else ''}")
        
        md_lines.append(content)
        md_lines.append("")
    
    # Add comments if any
    comments = storage.get_comments(req.conv_id)
    if comments:
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("## Notes & Comments")
        md_lines.append("")
        for c in comments:
            author = c.get("author", "You")
            msg = c.get("message", "")
            created_at = datetime.datetime.fromtimestamp(c.get("created_at", 0)).strftime('%Y-%m-%d %H:%M')
            md_lines.append(f"**{author}** ({created_at}): {msg}")
            md_lines.append("")
    
    return {
        "format": "markdown",
        "content": "\n".join(md_lines),
        "title": title
    }

@app.get("/api/export/{conv_id}")
async def export_conversation_get(conv_id: str, format: str = "markdown", user=Depends(require_auth)):
    """Export a conversation via GET (for download)."""
    req = ExportRequest(conv_id=conv_id, format=format)
    return await export_conversation(req, user)


# --- TTS ---

@app.post("/api/tts")
@limiter.limit("30/minute")
async def text_to_speech(request: Request, req: TTSRequest, user=Depends(require_auth)):
    if not req.text or len(req.text) > 3000:
        raise HTTPException(400, "Text must be between 1 and 3000 characters")
    if req.lang not in {"fr", "en", "es", "de", "it"}:
        req.lang = "fr"

    chunks = split_text_into_chunks(req.text)
    if not chunks:
        raise HTTPException(400, "No text to speak")

    async with httpx.AsyncClient(timeout=30.0) as client:
        async def fetch_chunk(chunk: str) -> bytes:
            url = (
                "https://translate.google.com/translate_tts"
                f"?ie=UTF-8&client=tw-ob&tl={req.lang}&q={urllib.parse.quote(chunk)}"
            )
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                logger.warning("TTS chunk request failed: status=%s url=%s", r.status_code, url[:80])
                raise HTTPException(502, f"TTS provider returned status {r.status_code}")
            return r.content

        try:
            # Download chunks concurrently; MP3 frames can be concatenated byte-wise.
            audio_parts = await asyncio.gather(*[fetch_chunk(c) for c in chunks])
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("TTS generation failed: %s", exc)
            raise HTTPException(500, "TTS generation failed") from exc

    if not any(audio_parts):
        raise HTTPException(502, "No audio generated")

    async def audio_stream():
        for part in audio_parts:
            yield part

    return StreamingResponse(audio_stream(), media_type="audio/mpeg")


# --- Knowledge Base (file upload) ---

@app.post("/api/upload")
@limiter.limit("10/minute")
async def upload_file(request: Request, file: UploadFile = File(...), user=Depends(require_auth)):
    # Validate extension
    filename = file.filename or "upload"
    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: .pdf, .txt, .md")

    # Validate content-type when provided
    if file.content_type and file.content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(400, f"Unsupported content type: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(400, f"File too large. Max size is {MAX_UPLOAD_SIZE // (1024 * 1024)} MB")

    text = ""
    if ext == '.pdf':
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = "".join(p.extract_text() or "" for p in reader.pages)
        except Exception:
            logger.warning("Could not read uploaded PDF: %s", filename)
            text = "Could not read PDF"
    else:
        text = content.decode('utf-8', errors='ignore')

    if text.strip():
        kb.add(filename, text)

    return {"filename": filename, "chunks": kb.count(), "status": "ok"}


@app.get("/api/knowledge")
async def get_knowledge(user=Depends(require_auth)):
    return {"count": kb.count(), "files": kb.filenames()}


# --- Clear ---

@app.delete("/api/history")
async def clear_history(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    user['conversations'] = {}
    storage.save_user(user)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
