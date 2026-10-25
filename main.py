import os
import time
import uuid
import secrets
import asyncio
import datetime
import urllib.parse
import logging
import logging.handlers
import re
import hashlib
import json
from dataclasses import asdict, replace
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Response, Request
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
import bcrypt
import jwt
import pyotp
import db
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.exc import IntegrityError
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

# The admin URL stays on this origin. Changing the path is only a discovery
# deterrent; authorization is enforced independently on every admin API.
ADMIN_PATH = os.getenv("ADMIN_PATH", "/parlez-admin").strip() or "/parlez-admin"
if (
    not ADMIN_PATH.startswith("/")
    or ADMIN_PATH == "/"
    or ADMIN_PATH in {"/api", "/login", "/static"}
    or not re.fullmatch(r"/[A-Za-z0-9/_-]+", ADMIN_PATH)
    or ADMIN_PATH.startswith("/api/")
):
    logger.error("Invalid ADMIN_PATH; using /parlez-admin")
    ADMIN_PATH = "/parlez-admin"
if ADMIN_PATH != "/" and ADMIN_PATH.endswith("/"):
    ADMIN_PATH = ADMIN_PATH.rstrip("/")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "").strip()
ADMIN_TOTP_SECRET = os.getenv("ADMIN_TOTP_SECRET", "").replace(" ", "").strip().upper()
ADMIN_SESSION_SECRET = os.getenv("ADMIN_SESSION_SECRET", "").strip()
try:
    ADMIN_SESSION_TTL_MINUTES = max(5, min(60, int(os.getenv("ADMIN_SESSION_TTL_MINUTES", "15"))))
except ValueError:
    ADMIN_SESSION_TTL_MINUTES = 15
try:
    ADMIN_TOTP_SECRET_VALID = bool(ADMIN_TOTP_SECRET and pyotp.TOTP(ADMIN_TOTP_SECRET).now())
except (ValueError, TypeError):
    ADMIN_TOTP_SECRET_VALID = False
ADMIN_PASSWORD_HASH_VALID = bool(
    re.fullmatch(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}", ADMIN_PASSWORD_HASH)
)
ADMIN_AUTH_CONFIGURED = bool(
    ADMIN_USERNAME
    and ADMIN_PASSWORD_HASH_VALID
    and ADMIN_TOTP_SECRET_VALID
    and len(ADMIN_SESSION_SECRET) >= 32
)
if any((ADMIN_USERNAME, ADMIN_PASSWORD_HASH, ADMIN_TOTP_SECRET, ADMIN_SESSION_SECRET)) and not ADMIN_AUTH_CONFIGURED:
    logger.error("Admin panel is disabled: complete all ADMIN_* authentication settings in .env")

from courses import conversation_scenarios, COURSE_CATALOG, COURSE_LEVEL_CATALOG
from courses.validation import validate_catalog, validate_course
from engine import build_system_prompt, detect_mode, find_lesson_context, LEVEL_NAMES

# Task 4.3 (A3 fix): build a {lesson_id: (course, unit, lesson)} index once
# at import time so handlers don't do full nested scans of all courses ×
# units × lessons on every request.
LESSON_INDEX: dict = {}
for _c in COURSE_CATALOG.values():
    for _u in _c.units:
        for _l in _u.lessons:
            LESSON_INDEX[_l.id] = (_c, _u, _l)

COURSE_DATA_ISSUES = validate_catalog(COURSE_CATALOG)
for _level, _issues in COURSE_DATA_ISSUES.items():
    logger.error("Course %s failed startup content validation: %s", _level, _issues[:10])


def serialize_lesson(lesson, course=None, unit=None) -> dict:
    """Task 4.3: one helper for the duplicated lesson-serialization
    dict-comprehension that was previously copy-pasted across endpoints.
    Pass course/unit when you have them; otherwise they're looked up in
    LESSON_INDEX (cheaper than re-walking the tree)."""
    if course is None or unit is None:
        hit = LESSON_INDEX.get(lesson.id)
        if hit is not None:
            course, unit, _ = hit
    return {
        'id': lesson.id,
        'title': lesson.title,
        'titleFr': lesson.titleFr,
        'description': lesson.description,
        'objectives': lesson.objectives,
        'skillTags': lesson.skillTags,
        'transferTask': lesson.transferTask,
        'selfCheck': lesson.selfCheck,
        'estimatedMinutes': lesson.estimatedMinutes,
        'vocabulary': [{'fr': v.fr, 'en': v.en, 'ipa': v.ipa, 'example': v.example} for v in lesson.vocabulary] if lesson.vocabulary else [],
        'grammar': [{'title': g.title, 'explanation': g.explanation, 'examples': [{'fr': e.fr, 'en': e.en} for e in g.examples]} for g in lesson.grammar] if lesson.grammar else [],
        'dialogue': [{'speaker': d.speaker, 'name': d.name, 'fr': d.fr, 'en': d.en} for d in lesson.dialogue] if lesson.dialogue else [],
        'culturalNote': lesson.culturalNote,
    }

from engine.exercises import check_answer
from engine.flashcards import create_flashcard, review_flashcard, get_due_cards, get_review_stats
from engine.practice import generate_vocab_quiz, generate_conj_quiz, generate_fill_blank_vocab, categorize_vocabulary, get_word_of_day
from engine.adaptive import analyze_weak_areas, get_difficulty_adjustments, build_adaptive_prompt_addition
from engine.content_ingestion import process_french_content
from engine.writing import build_writing_correction_prompt, parse_correction_response, format_correction_for_display
from mock_tests import mock_tests, get_test
from mock_tests.data import get_practice_set_questions, get_section_sets, get_all_section_sets, get_task, PRACTICE_SETS_COUNT

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

class RequestLoggingMiddleware:
    """Pure ASGI middleware for request logging.

    Implemented as a class instead of @app.middleware to avoid the
    Starlette BaseHTTPMiddleware + TestClient EndOfStream issue.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        start = time.time()
        request = Request(scope, receive)
        status_code = None

        async def wrapped_send(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, request.receive, wrapped_send)
            duration = round((time.time() - start) * 1000, 2)
            logger.info(
                "method=%s path=%s status=%s duration_ms=%s",
                request.method, request.url.path, status_code, duration,
            )
        except Exception as exc:
            duration = round((time.time() - start) * 1000, 2)
            logger.exception(
                "method=%s path=%s duration_ms=%s error=%s",
                request.method, request.url.path, duration, exc,
            )
            raise


class NoCacheMiddleware:
    """Pure ASGI middleware to disable caching for static and HTML responses."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope, receive)
        path = request.url.path

        async def wrapped_send(message):
            if (
                message["type"] == "http.response.start"
                and path.startswith(("/static/", "/"))
            ):
                headers = [
                    (k, v)
                    for k, v in message.get("headers", [])
                    if k.lower() != b"cache-control"
                ]
                headers.append(
                    (b"cache-control", b"no-cache, no-store, must-revalidate")
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, request.receive, wrapped_send)


class SecurityHeadersMiddleware:
    """Pure ASGI middleware to add baseline security headers.

    - CSP: blocks injected inline scripts until Task 2.1/2.2 land (uses
      'unsafe-inline' for scripts because app.js still has inline handlers).
      Tighten script-src to 'self' once Task 2.2 removes inline onclick.
    - X-Frame-Options / frame-ancestors: prevent clickjacking.
    - X-Content-Type-Options: stop MIME sniffing.
    - Referrer-Policy: don't leak full URLs to third parties.
    HSTS is set at the Caddy layer (see Caddyfile).
    """

    CSP = (
        "default-src 'self'; "
        "script-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' https://translate.google.com; "
        # TTS is fetched from our API and played through a local object URL.
        "media-src 'self' blob:; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"content-security-policy", self.CSP.encode("latin-1")))
                headers.append((b"x-frame-options", b"DENY"))
                headers.append((b"x-content-type-options", b"nosniff"))
                headers.append(
                    (b"referrer-policy", b"strict-origin-when-cross-origin")
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, wrapped_send)


# Add ASGI middlewares. FastAPI applies add_middleware in reverse order, so the
# last-added middleware is the outermost wrapper. We add security, then cache,
# then logging to preserve the previous @app.middleware execution order.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(NoCacheMiddleware)
app.add_middleware(RequestLoggingMiddleware)


class XP:
    """XP reward amounts used across endpoints."""

    CHAT_MESSAGE = 5
    EXERCISE_CORRECT = 10
    LESSON_COMPLETE = 50
    FLASHCARD_REVIEW = 5
    EXAM_QUESTION_CORRECT = 5
    WRITING_CORRECTION = 15


NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_NVIDIA_MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"
DEFAULT_AI_PROVIDER = os.getenv("AI_PROVIDER", "nvidia").strip().lower() or "nvidia"


def resolve_nvidia_model(configured_model: str | None = None) -> str:
    """Use NVIDIA_MODEL or the current text-model default."""
    if configured_model is None:
        configured_model = os.getenv("NVIDIA_MODEL")
    return (configured_model or "").strip() or DEFAULT_NVIDIA_MODEL


MODEL = resolve_nvidia_model()

# Provider endpoints are deliberately fixed in server code. The admin API
# accepts provider/model IDs, never arbitrary URLs (which would create an SSRF
# surface). API keys remain server-side in environment/secret configuration.
AI_PROVIDER_SPECS = {
    "nvidia": {
        "label": "NVIDIA NIM",
        "base_url": INVOKE_URL,
        "key_env": "NVIDIA_API_KEY",
        "default_model": MODEL,
    },
    "gemini": {
        "label": "Google Gemini API",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "key_env": "GEMINI_API_KEY",
        "default_model": os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash",
    },
    "openrouter": {
        "label": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "key_env": "OPENROUTER_API_KEY",
        "default_model": os.getenv("OPENROUTER_MODEL", "openrouter/free").strip() or "openrouter/free",
    },
    "opencode_zen": {
        "label": "OpenCode Zen",
        "base_url": "https://opencode.ai/zen/v1/chat/completions",
        "key_env": "OPENCODE_ZEN_API_KEY",
        "default_model": os.getenv("OPENCODE_ZEN_MODEL", "big-pickle").strip() or "big-pickle",
    },
}


def _provider_key(provider: str) -> str | None:
    spec = AI_PROVIDER_SPECS.get(provider)
    if not spec:
        return None
    if provider == "nvidia":
        key = NVIDIA_API_KEY or ""
    else:
        key = os.getenv(spec["key_env"], "").strip()
    if provider == "opencode_zen" and not key:
        key = os.getenv("OPENCODE_API_KEY", "").strip()
    return key or None


def _default_ai_config() -> dict:
    provider = DEFAULT_AI_PROVIDER if DEFAULT_AI_PROVIDER in AI_PROVIDER_SPECS else "nvidia"
    model = MODEL if provider == "nvidia" else AI_PROVIDER_SPECS[provider]["default_model"]
    return {"provider": provider, "model": model}


def get_active_ai_config() -> dict:
    """Read the DB-managed active model, falling back to deployment defaults."""
    saved = storage.get_setting("ai_config")
    if isinstance(saved, dict):
        provider = str(saved.get("provider", "")).strip().lower()
        model = str(saved.get("model", "")).strip()
        if provider in AI_PROVIDER_SPECS and model:
            return {"provider": provider, "model": model}
    return _default_ai_config()


def get_course_review_records() -> dict:
    """Load explicit, version-bound administrator review attestations."""
    saved = storage.get_setting("course_reviews", {})
    return saved if isinstance(saved, dict) else {}


def course_content_fingerprint(course) -> str:
    """Hash the full serialized curriculum so edits invalidate stale reviews."""
    material = json.dumps(asdict(course), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def get_current_course_review(level: str) -> Optional[dict]:
    """Return a review attestation only when it covers the current course version."""
    course = COURSE_CATALOG.get(level)
    record = get_course_review_records().get(level)
    if (
        course is not None
        and isinstance(record, dict)
        and record.get("reviewed") is True
        and record.get("version") == course.version
        and record.get("content_fingerprint") == course_content_fingerprint(course)
        and record.get("reviewer_name")
        and record.get("qualification")
    ):
        return record
    return None


def get_course_access_config() -> dict:
    """Load publication flags; only A1 is public until an admin enables more."""
    saved = storage.get_setting("course_access")
    if not isinstance(saved, dict):
        return {"enabled_levels": ["A1"], "enabled_units": {}}
    enabled = [
        str(level).upper()
        for level in saved.get("enabled_levels", ["A1"])
        if str(level).upper() in COURSE_CATALOG
    ]
    if "A1" not in enabled:
        enabled.insert(0, "A1")
    units = saved.get("enabled_units", {})
    return {"enabled_levels": list(dict.fromkeys(enabled)), "enabled_units": units if isinstance(units, dict) else {}}


def get_enabled_courses() -> list:
    """Return published course objects with only published units attached."""
    access = get_course_access_config()
    enabled = set(access["enabled_levels"])
    unit_flags = access["enabled_units"]
    result = []
    for level, course in COURSE_CATALOG.items():
        review_record = get_current_course_review(level) if level != "A1" else None
        if level not in enabled or level in COURSE_DATA_ISSUES:
            continue
        if level != "A1" and review_record is None:
            continue
        configured_units = unit_flags.get(level)
        if not isinstance(configured_units, list):
            configured_units = [unit.id for unit in course.units]
        configured_units = set(configured_units)
        visible_units = [unit for unit in course.units if unit.id in configured_units]
        if visible_units:
            effective_status = "reviewed" if review_record else course.contentStatus
            result.append(replace(course, units=visible_units, contentStatus=effective_status))
    return result


def get_public_course(level: str):
    normalized = str(level or "").upper()
    return next((course for course in get_enabled_courses() if course.level == normalized), None)


def require_public_course(level: str):
    course = get_public_course(level)
    if course is None:
        raise HTTPException(status_code=404, detail="Course level is not available")
    return course


def get_public_course_levels() -> list[dict]:
    enabled = {course.level: course for course in get_enabled_courses()}
    return [
        {
            **meta,
            "unitCount": len(enabled[meta["level"]].units),
            "lessonCount": sum(len(unit.lessons) for unit in enabled[meta["level"]].units),
            "contentStatus": enabled[meta["level"]].contentStatus,
            "version": enabled[meta["level"]].version,
        }
        for meta in COURSE_LEVEL_CATALOG
        if meta["level"] in enabled
    ]

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
    email: str
    username: str
    password: str
    name: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str
    totp: str


class AdminAIConfigUpdate(BaseModel):
    provider: str
    model: str


class AdminAITestRequest(BaseModel):
    provider: str
    model: str


class AdminCourseAccessUpdate(BaseModel):
    enabled_levels: list[str]
    enabled_units: dict[str, list[str]]


class AdminCourseReviewAttestation(BaseModel):
    reviewer_name: str
    qualification: str
    confirm_review: bool = False


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


def _admin_origin_is_same(request: Request) -> bool:
    """Reject explicit cross-origin admin requests; same-origin UI needs no CORS."""
    origin = request.headers.get("origin")
    if not origin:
        return True
    try:
        supplied = urllib.parse.urlsplit(origin)
        expected = urllib.parse.urlsplit(str(request.base_url))
        return supplied.scheme == expected.scheme and supplied.netloc == expected.netloc
    except ValueError:
        return False


def _decode_admin_session(request: Request):
    if not ADMIN_AUTH_CONFIGURED:
        raise HTTPException(status_code=503, detail="Admin access is not configured on this server.")
    token = request.cookies.get("parlez_admin")
    if not token:
        raise HTTPException(status_code=401, detail="Admin sign-in required.")
    try:
        payload = jwt.decode(token, ADMIN_SESSION_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Admin session expired. Sign in again.")
    if payload.get("scope") != "parlez_admin" or not secrets.compare_digest(
        str(payload.get("sub", "")), ADMIN_USERNAME
    ):
        raise HTTPException(status_code=401, detail="Admin session expired. Sign in again.")
    session_id = str(payload.get("jti", ""))
    if not session_id or not storage.admin_session_is_active(session_id, ADMIN_USERNAME):
        raise HTTPException(status_code=401, detail="Admin session expired. Sign in again.")
    return payload


def require_admin(request: Request):
    """Authorize admin APIs with a dedicated session and per-request CSRF check."""
    payload = _decode_admin_session(request)
    if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        supplied_csrf = request.headers.get("X-CSRF-Token", "")
        expected_csrf = str(payload.get("csrf", ""))
        if not expected_csrf or not secrets.compare_digest(supplied_csrf, expected_csrf):
            raise HTTPException(status_code=403, detail="Admin request could not be verified.")
        if not _admin_origin_is_same(request):
            raise HTTPException(status_code=403, detail="Cross-origin admin requests are not allowed.")
    return {"username": ADMIN_USERNAME, "csrf": payload["csrf"], "session_id": payload["jti"]}


DAILY_LLM_BUDGET = 100  # Task 3.9: per-user LLM request cap

def check_daily_llm_budget(user):
    """Enforce per-user daily LLM request cap. Mutates `user['llm_daily']`
    in-place; caller is responsible for save_user() if persistence is needed.

    Raises 429 when the cap is exceeded.
    """
    today = datetime.date.today().isoformat()
    llm_daily = user.setdefault('llm_daily', {'date': today, 'count': 0})
    if llm_daily.get('date') != today:
        llm_daily['date'] = today
        llm_daily['count'] = 0
    if llm_daily['count'] >= DAILY_LLM_BUDGET:
        raise HTTPException(
            status_code=429,
            detail=f"Daily AI tutor limit reached ({DAILY_LLM_BUDGET} requests/day). Resets at midnight UTC.",
        )
    llm_daily['count'] += 1
    return llm_daily['count']


async def call_ai_provider(messages, provider: str, model: str, max_tokens: int = 2048):
    """Call a configured OpenAI-compatible provider without exposing its key."""
    spec = AI_PROVIDER_SPECS.get(provider)
    api_key = _provider_key(provider)
    if not spec or not api_key:
        raise HTTPException(status_code=503, detail="The selected AI provider is not configured.")
    if not model or len(model) > 200:
        raise HTTPException(status_code=503, detail="The selected AI model is not configured correctly.")

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.6,
        "top_p": 0.95,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        last_error = "provider unavailable"
        for attempt in range(3):
            try:
                response = await client.post(
                    spec["base_url"],
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if response.status_code == 200:
                    return response.json()
                if response.status_code == 429 or response.status_code >= 500:
                    # Retry transient capacity/rate errors, but never log prompt or provider body.
                    last_error = f"{provider} returned HTTP {response.status_code}"
                    logger.warning("AI provider attempt %s failed: %s", attempt + 1, last_error)
                else:
                    logger.warning("AI provider rejected request: provider=%s status=%s", provider, response.status_code)
                    raise HTTPException(status_code=502, detail=f"AI request failed ({response.status_code}).")
            except httpx.RequestError as exc:
                last_error = f"{provider} request failed: {type(exc).__name__}"
                logger.warning("AI provider attempt %s failed: %s", attempt + 1, last_error)

            if attempt < 2:
                await asyncio.sleep(2 ** attempt)

        logger.error("AI provider failed after retries: %s", last_error)
        raise HTTPException(status_code=503, detail="AI service is temporarily unavailable. Please try again in a moment.")


async def call_nvidia(messages, max_tokens=2048):
    """Legacy call-site name; dispatches through the admin-selected provider."""
    config = get_active_ai_config()
    return await call_ai_provider(messages, config["provider"], config["model"], max_tokens)


# ============================================================
# ROUTES
# ============================================================

# Task 4.7 (A8): read the static HTML once at import time instead of
# blocking open() per request. The no-cache header still forces clients to
# revalidate, but the server-side cost is now a single file read at boot.
_LANDING_HTML = open("static/landing.html").read()
_INDEX_HTML = open("static/index.html").read()
_ADMIN_HTML = open("static/admin.html").read()


@app.get(ADMIN_PATH, response_class=HTMLResponse, include_in_schema=False)
async def admin_page():
    """Serve the same-origin admin shell; every sensitive action uses admin APIs."""
    return Response(
        content=_ADMIN_HTML,
        media_type="text/html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "X-Robots-Tag": "noindex, nofollow, noarchive"},
    )


@app.post("/api/admin/login", include_in_schema=False)
@limiter.limit("5/minute")
async def admin_login(request: Request, credentials: AdminLoginRequest, response: Response):
    """Password + TOTP login for the dedicated, environment-bootstrapped admin."""
    if not ADMIN_AUTH_CONFIGURED:
        raise HTTPException(status_code=503, detail="Admin access is not configured on this server.")
    if not _admin_origin_is_same(request) or request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(status_code=403, detail="Cross-origin admin sign-in is not allowed.")

    username_ok = secrets.compare_digest(credentials.username.strip(), ADMIN_USERNAME)
    password_ok = False
    totp_ok = False
    try:
        password_ok = bcrypt.checkpw(
            credentials.password.encode("utf-8"), ADMIN_PASSWORD_HASH.encode("utf-8")
        )
    except (ValueError, TypeError):
        password_ok = False
    try:
        code = credentials.totp.strip()
        if re.fullmatch(r"\d{6}", code):
            totp_ok = pyotp.TOTP(ADMIN_TOTP_SECRET).verify(code, valid_window=1)
    except (ValueError, TypeError):
        totp_ok = False

    if not (username_ok and password_ok and totp_ok):
        raise HTTPException(status_code=401, detail="Invalid admin credentials or verification code.")

    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = now + datetime.timedelta(minutes=ADMIN_SESSION_TTL_MINUTES)
    csrf_token = secrets.token_urlsafe(32)
    session_id = secrets.token_urlsafe(24)
    storage.create_admin_session(
        session_id,
        ADMIN_USERNAME,
        expires_at.timestamp(),
    )
    session_token = jwt.encode(
        {
            "sub": ADMIN_USERNAME,
            "scope": "parlez_admin",
            "csrf": csrf_token,
            "jti": session_id,
            "iat": now,
            "exp": expires_at,
        },
        ADMIN_SESSION_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    response.set_cookie(
        key="parlez_admin",
        value=session_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/api/admin",
        max_age=ADMIN_SESSION_TTL_MINUTES * 60,
    )
    storage.add_admin_audit(ADMIN_USERNAME, "admin_login", {})
    return {"ok": True}


@app.get("/api/admin/session", include_in_schema=False)
async def admin_session(admin=Depends(require_admin)):
    return {"username": admin["username"], "csrf_token": admin["csrf"]}


@app.post("/api/admin/logout", include_in_schema=False)
async def admin_logout(request: Request, response: Response, admin=Depends(require_admin)):
    payload = _decode_admin_session(request)
    storage.revoke_admin_session(str(payload.get("jti", "")))
    response.delete_cookie(key="parlez_admin", path="/api/admin", secure=COOKIE_SECURE, httponly=True, samesite="strict")
    storage.add_admin_audit(admin["username"], "admin_logout", {})
    return {"ok": True}


def _admin_ai_payload() -> dict:
    config = get_active_ai_config()
    providers = []
    for provider, spec in AI_PROVIDER_SPECS.items():
        providers.append({
            "id": provider,
            "label": spec["label"],
            "configured": bool(_provider_key(provider)),
            "default_model": spec["default_model"],
        })
    history = storage.get_setting("ai_config_history", [])
    can_rollback = isinstance(history, list) and bool(history)
    return {
        "provider": config["provider"],
        "model": config["model"],
        "providers": providers,
        "can_rollback": can_rollback,
    }


def _admin_course_payload() -> dict:
    access = get_course_access_config()
    configured_levels = set(access["enabled_levels"])
    unit_flags = access["enabled_units"]
    levels = []
    for level, course in COURSE_CATALOG.items():
        review_record = get_current_course_review(level) if level != "A1" else None
        is_enabled = level in configured_levels and (level == "A1" or review_record is not None)
        configured_units = unit_flags.get(level)
        if not isinstance(configured_units, list):
            configured_units = [unit.id for unit in course.units]
        configured_units = set(configured_units)
        lesson_count = sum(len(unit.lessons) for unit in course.units)
        release_warning = None
        if level != "A1" and review_record is None:
            release_warning = (
                f"{level} is unpublished draft content. A qualified French educator must review the current version "
                f"and record a review attestation before public release."
            )
        elif review_record is not None:
            release_warning = (
                f"Review attestation recorded for version {course.version} by {review_record['reviewer_name']} "
                f"({review_record['qualification']}). Verify the reviewer's credentials independently; this is not certification."
            )
        levels.append({
            "level": level,
            "title": course.title,
            "description": course.description,
            "content_status": "reviewed" if review_record is not None else course.contentStatus,
            "version": course.version,
            "level_outcomes": course.levelOutcomes,
            "review_status": "reviewed" if review_record is not None else "pending",
            "reviewer_name": review_record.get("reviewer_name") if review_record else None,
            "reviewer_qualification": review_record.get("qualification") if review_record else None,
            "reviewed_at": review_record.get("reviewed_at") if review_record else None,
            "enabled": is_enabled,
            "module_count": len(course.units),
            "lesson_count": lesson_count,
            "release_warning": release_warning,
            "units": [
                {
                    "id": unit.id,
                    "title": unit.title,
                    "lesson_count": len(unit.lessons),
                    "capstone": unit.capstone,
                    "enabled": unit.id in configured_units,
                }
                for unit in course.units
            ],
        })
    return {"enabled_levels": sorted(level["level"] for level in levels if level["enabled"]), "levels": levels}


@app.get("/api/admin/config", include_in_schema=False)
async def admin_config(admin=Depends(require_admin)):
    return {
        "ai": _admin_ai_payload(),
        "courses": _admin_course_payload(),
        "admin_path": ADMIN_PATH,
        "storage": "shared-database-settings",
    }


@app.put("/api/admin/ai", include_in_schema=False)
async def update_admin_ai_config(config: AdminAIConfigUpdate, admin=Depends(require_admin)):
    provider = config.provider.strip().lower()
    model = config.model.strip()
    if provider not in AI_PROVIDER_SPECS:
        raise HTTPException(status_code=400, detail="Unsupported AI provider.")
    if not model or len(model) > 200 or any(ord(char) < 32 for char in model):
        raise HTTPException(status_code=400, detail="Enter a valid model ID (1–200 characters).")
    if not _provider_key(provider):
        raise HTTPException(status_code=400, detail="That provider has no API key configured on the server.")

    previous = get_active_ai_config()
    selected = {"provider": provider, "model": model}
    changed = selected != previous
    test_key = f"ai_provider_test:{admin['session_id']}"
    tested = storage.get_setting(test_key)
    if changed and not (
        isinstance(tested, dict)
        and tested.get("provider") == provider
        and tested.get("model") == model
        and time.time() - float(tested.get("tested_at", 0)) <= 300
    ):
        raise HTTPException(status_code=400, detail="Run a successful connection test for this exact provider/model before saving.")

    history = storage.get_setting("ai_config_history", [])
    if not isinstance(history, list):
        history = []
    if changed:
        history = (history + [previous])[-10:]
        storage.set_settings({"ai_config": selected, "ai_config_history": history})
        storage.delete_setting(test_key)
        storage.add_admin_audit(admin["username"], "ai_config_updated", {
            "previous_provider": previous["provider"],
            "previous_model": previous["model"],
            "provider": provider,
            "model": model,
        })
    return _admin_ai_payload()


@app.post("/api/admin/ai/test", include_in_schema=False)
@limiter.limit("5/minute")
async def test_admin_ai_provider(request: Request, test: AdminAITestRequest, admin=Depends(require_admin)):
    provider = test.provider.strip().lower()
    model = test.model.strip()
    if provider not in AI_PROVIDER_SPECS:
        raise HTTPException(status_code=400, detail="Unsupported AI provider.")
    if not model or len(model) > 200 or any(ord(char) < 32 for char in model):
        raise HTTPException(status_code=400, detail="Enter a valid model ID (1–200 characters).")
    if not _provider_key(provider):
        raise HTTPException(status_code=400, detail="That provider has no API key configured on the server.")

    result = await call_ai_provider(
        [{"role": "user", "content": "Reply with exactly: Parlez connection test passed."}],
        provider,
        model,
        max_tokens=40,
    )
    try:
        message = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise HTTPException(status_code=502, detail="Provider responded, but returned an unexpected chat-completions result.")
    storage.set_setting(f"ai_provider_test:{admin['session_id']}", {
        "provider": provider,
        "model": model,
        "tested_at": time.time(),
    })
    storage.add_admin_audit(admin["username"], "ai_provider_tested", {"provider": provider, "model": model})
    return {"ok": True, "provider": provider, "model": model, "message": str(message)[:240]}


@app.post("/api/admin/ai/rollback", include_in_schema=False)
async def rollback_admin_ai_config(admin=Depends(require_admin)):
    history = storage.get_setting("ai_config_history", [])
    if not isinstance(history, list) or not history:
        raise HTTPException(status_code=400, detail="No previous AI configuration is available to restore.")
    previous = history[-1]
    if not isinstance(previous, dict) or previous.get("provider") not in AI_PROVIDER_SPECS or not previous.get("model"):
        raise HTTPException(status_code=409, detail="The saved previous AI configuration is invalid.")
    if not _provider_key(previous["provider"]):
        raise HTTPException(status_code=400, detail="The previous provider key is no longer configured; rollback is unavailable.")

    current = get_active_ai_config()
    history = history[:-1]
    storage.set_settings({"ai_config": previous, "ai_config_history": history})
    storage.add_admin_audit(admin["username"], "ai_config_rolled_back", {
        "from_provider": current["provider"],
        "from_model": current["model"],
        "to_provider": previous["provider"],
        "to_model": previous["model"],
    })
    return _admin_ai_payload()


@app.get("/api/admin/courses", include_in_schema=False)
async def admin_courses(admin=Depends(require_admin)):
    return _admin_course_payload()


@app.post("/api/admin/courses/{level}/review", include_in_schema=False)
async def attest_course_review(level: str, review: AdminCourseReviewAttestation, admin=Depends(require_admin)):
    normalized = level.strip().upper()
    course = COURSE_CATALOG.get(normalized)
    if course is None or normalized == "A1":
        raise HTTPException(status_code=404, detail="Review attestation is only available for draft course levels.")
    if not review.confirm_review:
        raise HTTPException(status_code=400, detail="Confirm the qualified-educator review before recording the attestation.")
    reviewer_name = review.reviewer_name.strip()
    qualification = review.qualification.strip()
    if len(reviewer_name) < 2 or len(reviewer_name) > 120:
        raise HTTPException(status_code=400, detail="Enter the reviewer’s name (2–120 characters).")
    if len(qualification) < 10 or len(qualification) > 300:
        raise HTTPException(status_code=400, detail="Describe the reviewer’s relevant French-language education qualification (10–300 characters).")
    integrity_issues = validate_course(course)
    if integrity_issues:
        logger.error("Refusing review attestation for invalid %s course content: %s", normalized, integrity_issues[:10])
        raise HTTPException(status_code=409, detail=f"{normalized} course content failed integrity checks and cannot be reviewed for release.")

    # A legacy/stale publication flag must not turn a newly reviewed version
    # live automatically. Require an explicit second admin action to publish.
    if get_current_course_review(normalized) is None:
        previous_access = get_course_access_config()
        if normalized in previous_access["enabled_levels"]:
            storage.set_setting("course_access", {
                "enabled_levels": [item for item in previous_access["enabled_levels"] if item != normalized],
                "enabled_units": previous_access["enabled_units"],
            })

    record = {
        "reviewed": True,
        "version": course.version,
        "content_fingerprint": course_content_fingerprint(course),
        "reviewer_name": reviewer_name,
        "qualification": qualification,
        "reviewed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    review_records = get_course_review_records()
    review_records[normalized] = record
    storage.set_setting("course_reviews", review_records)
    storage.add_admin_audit(admin["username"], "course_review_attested", {
        "level": normalized,
        "version": course.version,
        "reviewer_name": reviewer_name,
    })
    return _admin_course_payload()


@app.put("/api/admin/courses", include_in_schema=False)
async def update_admin_courses(config: AdminCourseAccessUpdate, admin=Depends(require_admin)):
    requested_levels = {str(level).strip().upper() for level in config.enabled_levels}
    unknown_levels = requested_levels - set(COURSE_CATALOG)
    if unknown_levels:
        raise HTTPException(status_code=400, detail="One or more course levels are unknown.")
    if "A1" not in requested_levels:
        raise HTTPException(status_code=400, detail="A1 must remain published as the foundation level.")

    normalized_units: dict[str, list[str]] = {}
    for level, course in COURSE_CATALOG.items():
        selected = config.enabled_units.get(level, [unit.id for unit in course.units])
        if not isinstance(selected, list):
            raise HTTPException(status_code=400, detail=f"Invalid module selection for {level}.")
        selected_ids = {str(unit_id) for unit_id in selected}
        valid_ids = {unit.id for unit in course.units}
        if selected_ids - valid_ids:
            raise HTTPException(status_code=400, detail=f"Unknown module in {level}.")
        if level in requested_levels and not selected_ids:
            raise HTTPException(status_code=400, detail=f"Select at least one module before enabling {level}.")
        if level in requested_levels and level != "A1" and get_current_course_review(level) is None:
            raise HTTPException(status_code=409, detail=f"{level} is still unpublished. Record a current qualified-educator review attestation first.")
        if level in requested_levels:
            integrity_issues = validate_course(course)
            if integrity_issues:
                logger.error("Refusing to publish invalid %s course content: %s", level, integrity_issues[:10])
                raise HTTPException(status_code=409, detail=f"{level} course content failed integrity checks and cannot be published.")
        normalized_units[level] = [unit.id for unit in course.units if unit.id in selected_ids]

    previous = get_course_access_config()
    saved = {
        "enabled_levels": [level for level in COURSE_CATALOG if level in requested_levels],
        "enabled_units": normalized_units,
    }
    storage.set_setting("course_access", saved)
    storage.add_admin_audit(admin["username"], "course_publication_updated", {
        "enabled_levels": saved["enabled_levels"],
        "previous_enabled_levels": previous["enabled_levels"],
        "enabled_modules": {level: len(ids) for level, ids in normalized_units.items()},
    })
    return _admin_course_payload()


@app.get("/api/admin/audit", include_in_schema=False)
async def admin_audit(limit: int = 50, admin=Depends(require_admin)):
    return storage.list_admin_audit(limit)


@app.get("/api/admin/health", include_in_schema=False)
async def admin_health(admin=Depends(require_admin)):
    database = "connected"
    try:
        with storage.engine.connect() as connection:
            connection.execute(db.text("SELECT 1"))
    except Exception:
        logger.exception("Admin dashboard database health check failed")
        database = "unavailable"
    active_ai = get_active_ai_config()
    return {
        "backend": "healthy" if database == "connected" else "degraded",
        "database": database,
        "active_provider": active_ai["provider"],
        "active_model": active_ai["model"],
        "provider_key_configured": bool(_provider_key(active_ai["provider"])),
    }


@app.get("/", response_class=HTMLResponse)
async def root():
    return Response(content=_LANDING_HTML, media_type="text/html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return Response(content=_INDEX_HTML, media_type="text/html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


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
    # Validate syntax without DNS/network dependency. This does NOT prove inbox ownership.
    try:
        email = validate_email(req.email.strip(), check_deliverability=False, allow_smtputf8=False).normalized.casefold()
    except EmailNotValidError:
        raise HTTPException(400, "Please enter a valid email address")
    if len(email) > 254:
        raise HTTPException(400, "Email address must be at most 254 characters")
    if storage.email_exists(email):
        raise HTTPException(409, "Email address already registered. Please log in.")

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
    
    if len(req.password.encode('utf-8')) > 72:
        raise HTTPException(400, "Password must be at most 72 UTF-8 bytes")

    # Hash password
    password_hash = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create user
    try:
        user = storage.create_user(req.username, password_hash, req.name, email=email)
    except IntegrityError:
        # Unique DB constraints are authoritative if two requests race the prechecks.
        raise HTTPException(409, "Username or email address already registered. Please log in.")
    
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
async def get_me(user=Depends(require_auth)):
    """Get current user info."""
    return {
        "id": user['id'],
        "username": user['username'],
        "name": user['name'],
        "level": user['level']
    }


# --- Course API ---

@app.get("/api/courses")
async def get_courses():
    return get_public_course_levels()

@app.get("/api/courses/{level}")
async def get_course_detail(level: str):
    course = require_public_course(level)
    return {
        'level': course.level, 'title': course.title, 'book': course.book,
        'description': course.description, 'cefrDescription': course.cefrDescription,
        'color': course.color, 'version': course.version,
        'contentStatus': course.contentStatus, 'levelOutcomes': course.levelOutcomes,
        'units': [{
            'id': u.id, 'title': u.title, 'titleFr': u.titleFr,
            'theme': u.theme, 'description': u.description,
            'outcomes': u.outcomes, 'skillTags': u.skillTags,
            'capstone': u.capstone, 'capstoneCriteria': u.capstoneCriteria,
            'lessons': [{
                'id': l.id, 'title': l.title, 'titleFr': l.titleFr,
                'description': l.description, 'objectives': l.objectives,
                'skillTags': l.skillTags, 'transferTask': l.transferTask,
                'selfCheck': l.selfCheck,
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
    course = require_public_course(level)
    for unit in course.units:
        for lesson in unit.lessons:
            if lesson.id == lesson_id:
                return {
                    'id': lesson.id, 'title': lesson.title, 'titleFr': lesson.titleFr,
                    'description': lesson.description, 'objectives': lesson.objectives,
                    'skillTags': lesson.skillTags, 'transferTask': lesson.transferTask,
                    'selfCheck': lesson.selfCheck,
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
async def get_user(user=Depends(require_auth)):
    level = user.get('level', 'A1')
    if not get_public_course(level):
        level = 'A1'
    return {"level": level, "name": user.get('name', ''), "username": user.get('username', '')}

@app.post("/api/user")
async def update_user(settings: UserSettings, user=Depends(require_auth)):
    if settings.level:
        requested_level = settings.level.upper()
        if not get_public_course(requested_level):
            raise HTTPException(status_code=400, detail="That course level is not currently available.")
        user['level'] = requested_level
    if settings.name: user['name'] = settings.name
    storage.save_user(user)
    return {"level": user.get('level', 'A1'), "name": user.get('name', ''), "username": user.get('username', '')}


# --- Conversations ---

@app.get("/api/conversations")
async def get_conversations(user=Depends(require_auth)):
    convs = user.get('conversations', {})
    return sorted(convs.values(), key=lambda x: x.get("updated", 0), reverse=True)

@app.post("/api/conversations")
async def create_conversation(conv: ConversationCreate, user=Depends(require_auth)):
    conv_id = str(uuid.uuid4())[:8]
    level = (conv.level or user.get('level', 'A1')).upper()
    if not get_public_course(level):
        if conv.level:
            raise HTTPException(status_code=400, detail="That course level is not currently available.")
        level = 'A1'
    user.setdefault('conversations', {})[conv_id] = {
        "id": conv_id, "title": conv.title or "New Chat",
        "level": level, "messages": [],
        "created": time.time(), "updated": time.time()
    }
    storage.save_user(user)
    return user['conversations'][conv_id]

@app.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: str, user=Depends(require_auth)):
    conv = user.get('conversations', {}).get(conv_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return conv

@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str, user=Depends(require_auth)):
    convs = user.get('conversations', {})
    if conv_id not in convs:
        raise HTTPException(404, "Conversation not found")
    del convs[conv_id]
    storage.save_user(user)
    return {"ok": True}


# --- Chat ---

@app.post("/api/chat")
@limiter.limit("30/minute")
async def chat(request: Request, msg: ChatMessage, user=Depends(require_auth)):
    # Task 3.9: per-user daily LLM budget. Increments the counter; raises
    # 429 if the user has exceeded DAILY_LLM_BUDGET for today.
    check_daily_llm_budget(user)

    message = validate_user_text(msg.message, MAX_CHAT_MESSAGE_LENGTH, "message")
    
    level = (msg.level or user.get('level', 'A1')).upper()
    if not get_public_course(level):
        if msg.level:
            raise HTTPException(status_code=400, detail="That course level is not currently available.")
        level = 'A1'
    active_courses = get_enabled_courses()
    
    # Detect mode from message
    mode = msg.mode or detect_mode(message, level)
    
    # Find lesson context if needed
    lesson_ctx = None
    if msg.lesson_id:
        for course in active_courses:
            if course.level != level:
                continue
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
        lesson_ctx = find_lesson_context(message, active_courses)
    
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
    except HTTPException:
        raise
    except Exception:
        # Don't leak exception text to the client (fixes S11). Mirror the
        # /api/writing/correct pattern: log internally, return a generic 503,
        # and do NOT persist a fake assistant reply or award XP.
        logger.exception("Chat LLM call failed")
        raise HTTPException(
            status_code=503,
            detail="The tutor is temporarily unavailable. Please try again.",
        )
    
    # Save to conversation (in memory only — single save_user below)
    user_convs = user.get('conversations', {})
    if msg.conv_id and msg.conv_id in user_convs:
        user_convs[msg.conv_id]["messages"].append({"role": "user", "content": message})
        user_convs[msg.conv_id]["messages"].append({"role": "assistant", "content": resp})
        user_convs[msg.conv_id]["updated"] = time.time()
        if not user_convs[msg.conv_id].get("title_set"):
            user_convs[msg.conv_id]["title"] = message[:50]

    # Update XP
    progress = user.setdefault('progress', {"xp": 0, "streak": 0, "best_streak": 0, "last_active": None})
    progress['xp'] = progress.get('xp', 0) + XP.CHAT_MESSAGE
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

    # Single save_user at the end halves the lost-update race window (Task 3.1).
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
async def check_exercise(req: ExerciseCheck, user=Depends(require_auth)):
    exercise = req.exercise_data or {}
    is_correct, explanation = check_answer(exercise, req.answer)
    
    progress = user.setdefault('progress', {"xp": 0})
    if is_correct:
        progress['xp'] = progress.get('xp', 0) + XP.EXERCISE_CORRECT
    
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
async def get_exercise_history(limit: int = 50, user=Depends(require_auth)):
    return user.get('exercise_history', [])[-limit:]

@app.get("/api/exercise-stats")
async def get_exercise_stats(user=Depends(require_auth)):
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
async def get_progress(user=Depends(require_auth)):
    return user.get('progress', {})

@app.post("/api/progress/complete-lesson")
async def complete_lesson(data: dict, user=Depends(require_auth)):
    lesson_id = data.get('lesson_id')
    score = data.get('score', 0)
    progress = user.setdefault('progress', {})
    if lesson_id and lesson_id not in progress.get('lessons_completed', []):
        progress.setdefault('lessons_completed', []).append(lesson_id)
        progress['xp'] = progress.get('xp', 0) + XP.LESSON_COMPLETE
    storage.save_user(user)
    return progress

@app.get("/api/streaks")
async def get_streaks(user=Depends(require_auth)):
    """Return the current streak as stored. Read-only (Task 4.4): streak
    mutations live in /api/chat (and other action endpoints), not here.
    Calling GET twice in a row must NOT change stored state."""
    progress = user.get('progress', {})
    return {
        "current": progress.get("streak", 0),
        "best": progress.get("best_streak", 0),
        "last_active": progress.get("last_active"),
    }


# --- Flashcards ---

@app.get("/api/flashcards")
async def get_all_flashcards(user=Depends(require_auth)):
    return list(user.get('flashcards', {}).values())

@app.get("/api/flashcards/due")
async def get_due_flashcards(user=Depends(require_auth)):
    cards = list(user.get('flashcards', {}).values())
    return get_due_cards(cards)

@app.get("/api/flashcards/stats")
async def get_flashcard_stats(user=Depends(require_auth)):
    cards = list(user.get('flashcards', {}).values())
    return get_review_stats(cards)

@app.post("/api/flashcards")
async def create_flashcard_endpoint(req: FlashcardCreate, user=Depends(require_auth)):
    card = create_flashcard(
        front=req.front, back=req.back, card_type=req.card_type,
        level=req.level or user.get('level', 'A1'),
        lesson_id=req.lesson_id, meta=req.meta
    )
    user.setdefault('flashcards', {})[card['id']] = card
    storage.save_user(user)
    return card

@app.post("/api/flashcards/bulk")
async def create_bulk_flashcards(cards: list[FlashcardCreate], user=Depends(require_auth)):
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
async def review_flashcard_endpoint(card_id: str, req: FlashcardReview, user=Depends(require_auth)):
    user_flashcards = user.get('flashcards', {})
    if card_id not in user_flashcards:
        raise HTTPException(404, "Card not found")
    card = review_flashcard(user_flashcards[card_id], req.quality)
    user_flashcards[card_id] = card
    progress = user.setdefault('progress', {"xp": 0})
    progress['xp'] = progress.get('xp', 0) + XP.FLASHCARD_REVIEW
    storage.save_user(user)
    return {"card": card, "xp_earned": 5, "total_xp": progress.get('xp', 0)}

@app.delete("/api/flashcards/{card_id}")
async def delete_flashcard(card_id: str, user=Depends(require_auth)):
    user_flashcards = user.get('flashcards', {})
    if card_id in user_flashcards:
        del user_flashcards[card_id]
        storage.save_user(user)
    return {"ok": True}

@app.delete("/api/flashcards")
async def clear_flashcards(user=Depends(require_auth)):
    user['flashcards'] = {}
    storage.save_user(user)
    return {"ok": True}


# --- Vocabulary Practice ---

@app.post("/api/practice/lesson/{level}/{lesson_id}")
async def lesson_practice(level: str, lesson_id: str):
    """Generate a full practice set from a lesson's exercises."""
    course = require_public_course(level)
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
    course = require_public_course(req.level)
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
    course = require_public_course(req.level)
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
    course = require_public_course(req.level)
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
             'formatSourceUrl': t.formatSourceUrl, 'practiceNotice': t.practiceNotice,
             'sections': [{'id': s.id, 'title': s.title, 'titleFr': s.titleFr, 'description': s.description,
                           'icon': s.icon, 'questionCount': s.questionCount, 'officialQuestionCount': s.officialQuestionCount,
                           'officialTaskCount': s.officialTaskCount, 'durationMinutes': s.durationMinutes,
                           'tasks': [asdict(task) for task in s.tasks]}
                          for s in t.sections]} for t in mock_tests]

@app.get("/api/mock-tests/{test_type}")
async def get_mock_test(test_type: str):
    """Get a mock test with all questions."""
    test = get_test(test_type)
    return {
        'type': test.type, 'name': test.name, 'fullName': test.fullName,
        'description': test.description, 'color': test.color,
        'administeredBy': test.administeredBy, 'usedFor': test.usedFor,
        'formatSourceUrl': test.formatSourceUrl, 'practiceNotice': test.practiceNotice,
        'sections': [{
            'id': s.id, 'title': s.title, 'titleFr': s.titleFr,
            'description': s.description, 'icon': s.icon,
            'questionCount': s.questionCount, 'officialQuestionCount': s.officialQuestionCount,
            'officialTaskCount': s.officialTaskCount, 'durationMinutes': s.durationMinutes,
            'tasks': [asdict(task) for task in s.tasks],
            'questions': [{'id': q.id, 'type': q.type, 'prompt': q.prompt, 'promptFr': q.promptFr,
                           'options': q.options, 'audioText': q.audioText, 'level': q.level}
                          for q in s.questions]
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
                'questionCount': s.questionCount, 'officialQuestionCount': s.officialQuestionCount,
                'officialTaskCount': s.officialTaskCount, 'durationMinutes': s.durationMinutes,
                'tasks': [asdict(task) for task in s.tasks],
                'questions': [{'id': q.id, 'type': q.type, 'prompt': q.prompt, 'promptFr': q.promptFr,
                               'options': q.options, 'audioText': q.audioText, 'level': q.level}
                              for q in s.questions]
            }
    raise HTTPException(404, "Section not found")

@app.post("/api/mock-tests/{test_type}/submit")
async def submit_test(test_type: str, data: dict, user=Depends(require_auth)):
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
    
    result = {
        'testType': test.type, 'section': section_id or 'all',
        'score': score, 'correct': correct, 'total': total,
        'durationSec': duration_sec,
        'scoreNote': 'Accuracy on included practice questions only; open writing/speaking tasks are not scored. This is not an official TEF/TCF score or CEFR/NCLC level estimate.',
        'takenAt': datetime.datetime.now().isoformat(),
        'details': details,
    }

    user.setdefault('test_results', []).append(result)
    # Cap test_results (Task 3.1): bounds blast radius of any lost-update, and
    # keeps the JSON blob size bounded for the whole save.
    if len(user['test_results']) > 500:
        user['test_results'] = user['test_results'][-500:]
    progress = user.setdefault('progress', {"xp": 0})
    progress['xp'] = progress.get('xp', 0) + (correct * XP.EXAM_QUESTION_CORRECT)
    storage.save_user(user)
    
    return result

@app.get("/api/test-results")
async def get_test_results(limit: int = 20, user=Depends(require_auth)):
    results = user.get('test_results', [])[-max(1, min(limit, 100)):]
    return [{key: value for key, value in result.items() if key not in {'level', 'levelBreakdown'}} for result in results]

@app.get("/api/test-results/stats")
async def get_test_stats(user=Depends(require_auth)):
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
        'formatSourceUrl': test.formatSourceUrl,
        'practiceNotice': test.practiceNotice,
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
                'questionCount': s.officialQuestionCount,
                'taskCount': s.officialTaskCount,
                'durationMinutes': s.durationMinutes,
                'tasks': [asdict(task) for task in s.tasks],
                'sets': get_section_sets(test_type, section_id),
            }
    raise HTTPException(404, "Section not found")

@app.get("/api/exam/tasks/{test_type}/{section_id}/{task_id}")
async def get_exam_task(test_type: str, section_id: str, task_id: str):
    """Get an original, unscored writing or speaking practice task."""
    test = get_test(test_type.upper())
    task = get_task(test_type, section_id, task_id)
    if task is None:
        raise HTTPException(404, "Practice task not found")
    section = next((item for item in test.sections if item.id == section_id), None)
    return {
        'testType': test.type,
        'testName': test.name,
        'section': section_id,
        'sectionTitle': section.title if section else section_id,
        'sectionDurationMinutes': section.durationMinutes if section else None,
        'formatSourceUrl': test.formatSourceUrl,
        'practiceNotice': test.practiceNotice,
        'task': task,
    }

@app.get("/api/exam/questions/{test_type}/{section_id}/{set_num}")
@limiter.limit("30/minute")
async def get_exam_questions(request: Request, test_type: str, section_id: str, set_num: int):
    """Get questions for a specific practice set."""
    if set_num < 1 or set_num > PRACTICE_SETS_COUNT:
        raise HTTPException(400, f"Set number must be 1-{PRACTICE_SETS_COUNT}")
    
    questions = get_practice_set_questions(test_type, section_id, set_num)
    if not questions:
        return {"questions": [], "message": "No questions available for this set. Try sets 1-3."}

    # Task 3.6 (S7 fix): strip answer+explanation so users can't read them in
    # the network tab. The submit endpoint returns them with grading.
    sanitized = [
        {k: v for k, v in q.items() if k not in ('answer', 'explanation')}
        for q in questions
    ]
    return {"questions": sanitized, "total": len(sanitized)}

@app.post("/api/exam/submit/{test_type}/{section_id}/{set_num}")
@limiter.limit("20/minute")
async def submit_exam(request: Request, test_type: str, section_id: str, set_num: int, data: dict, user=Depends(require_auth)):
    """Submit exam answers and get results with level estimation."""
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
        })
    
    score = round((correct / total) * 100) if total > 0 else 0
    
    result = {
        'testType': test_type.upper(),
        'section': section_id,
        'setNum': set_num,
        'score': score,
        'correct': correct,
        'total': total,
        'durationSec': duration_sec,
        'scoreNote': 'Practice-item accuracy only; this is not an official TEF/TCF score or CEFR/NCLC level estimate.',
        'takenAt': datetime.datetime.now().isoformat(),
        'details': details,
    }

    user.setdefault('test_results', []).append(result)
    # Cap test_results (Task 3.1): bounds blast radius of any lost-update, and
    # keeps the JSON blob size bounded for the whole save.
    if len(user['test_results']) > 500:
        user['test_results'] = user['test_results'][-500:]
    progress = user.setdefault('progress', {"xp": 0})
    progress['xp'] = progress.get('xp', 0) + (correct * XP.EXAM_QUESTION_CORRECT)
    storage.save_user(user)
    
    return result

@app.get("/api/exam/history/{test_type}")
async def get_exam_history(test_type: str, user=Depends(require_auth)):
    """Get practice history without legacy, unsupported level estimates."""
    results = user.get('test_results', [])
    return [
        {key: value for key, value in result.items() if key not in {'level', 'levelBreakdown'}}
        for result in results
        if result.get('testType') == test_type.upper()
    ]

@app.get("/api/adaptive/analysis")
async def get_adaptive_analysis(user=Depends(require_auth)):
    """Get adaptive difficulty analysis for the current user."""
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
async def correct_writing(req: WritingCorrectionRequest, user=Depends(require_auth)):
    """Correct French writing with inline annotations."""
    # Task 3.9: per-user daily LLM budget.
    check_daily_llm_budget(user)

    text = validate_user_text(req.text, MAX_WRITING_TEXT_LENGTH, "text")
    level = (req.level or user.get('level', 'A1')).upper()
    if not get_public_course(level):
        if req.level:
            raise HTTPException(status_code=400, detail="That course level is not currently available.")
        level = 'A1'
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
    progress['xp'] = progress.get('xp', 0) + XP.WRITING_CORRECTION
    storage.save_user(user)
    
    return {
        "response": resp,
        "correction": correction,
        "formatted": formatted,
        "xp_earned": 15,
        "total_xp": progress.get('xp', 0),
    }


@app.post("/api/content/ingest")
async def ingest_content(req: ContentIngestRequest, user=Depends(require_auth)):
    """Process French text content to extract vocabulary, flashcards, and quizzes."""
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
async def get_exam_stats(test_type: str, user=Depends(require_auth)):
    """Get detailed stats for a test type."""
    results = [r for r in user.get('test_results', []) if r.get('testType') == test_type.upper()]
    
    if not results:
        return {'total': 0, 'avg_score': 0, 'best_score': 0, 'by_section': {}, 'recent': [],
                'scoreNote': 'Practice-item accuracy only; not an official TEF/TCF score or CEFR/NCLC level estimate.'}
    
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
    
    recent = [
        {key: value for key, value in result.items() if key not in {'level', 'levelBreakdown'}}
        for result in results[-5:]
    ]
    return {
        'total': len(results),
        'avg_score': round(sum(scores) / len(scores)),
        'best_score': max(scores),
        'by_section': by_section,
        'recent': recent,
        'scoreNote': 'Practice-item accuracy only; not an official TEF/TCF score or CEFR/NCLC level estimate.',
    }


@app.get("/api/practice/word-of-day")
async def word_of_day(user=Depends(require_auth)):
    course = get_public_course(user.get('level', 'A1')) or require_public_course('A1')
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
    course = require_public_course(level)
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
async def add_comment(req: CommentCreate, user=Depends(require_auth)):
    # Ownership check (fixes IDOR S4): only the conversation owner can comment on it.
    if req.conv_id not in user.get("conversations", {}):
        raise HTTPException(status_code=404, detail="Conversation not found")

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
    # Ownership check (fixes IDOR S4): don't leak comments on conversations
    # the caller doesn't own.
    if conv_id not in user.get("conversations", {}):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return storage.get_comments(conv_id)

@app.delete("/api/comments/{conv_id}/{comment_id}")
async def delete_comment(conv_id: str, comment_id: str, user=Depends(require_auth)):
    # Ownership check (fixes IDOR S4): caller must own the conversation.
    # We also restrict to comments authored by the caller, so users can't
    # delete each other's comments even on their own thread.
    if conv_id not in user.get("conversations", {}):
        raise HTTPException(status_code=404, detail="Conversation not found")
    existing = storage.get_comments(conv_id)
    target = next((c for c in existing if c.get("id") == comment_id), None)
    if not target or target.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Comment not found")
    storage.delete_comment(conv_id, comment_id)
    return {"ok": True}

@app.post("/api/share")
async def create_share(req: ShareCreate, user=Depends(require_auth)):
    user_convs = user.get('conversations', {})
    if req.conv_id not in user_convs:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = user_convs[req.conv_id]
    share_id = secrets.token_urlsafe(32)  # unguessable; fixes S6 (32-bit IDOR via enumeration)

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
async def list_shared(user=Depends(require_auth)):
    return storage.list_shared_by_user(user['id'])

@app.delete("/api/share/{share_id}")
async def delete_share(share_id: str, user=Depends(require_auth)):
    # Ownership check (fixes IDOR S5): only the share's creator may delete it.
    # 404 (not 403) to avoid disclosing that the share exists.
    share = storage.get_shared(share_id)
    if not share or share.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Not found")
    storage.delete_shared(share_id)
    return {"ok": True}

@app.post("/api/export")
async def export_conversation(req: ExportRequest, user=Depends(require_auth)):
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
    if not req.text.strip() or len(req.text) > 3000:
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
            if not r.content or not r.headers.get("content-type", "").lower().startswith("audio/"):
                logger.warning("TTS provider returned empty or non-audio content")
                raise HTTPException(502, "TTS provider did not return valid audio")
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



# --- Clear ---

@app.delete("/api/history")
async def clear_history(user=Depends(require_auth)):
    user['conversations'] = {}
    storage.save_user(user)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    # Task 3.2: SQLite + the in-memory rate limiter (main.storage.session /
    # app.state.limiter) are per-process. Do NOT set workers>1 without
    # first migrating storage to Postgres and switching the limiter to a
    # shared backend (e.g. Redis). See docker-compose.prod.yml for the
    # single-replica constraint.
    #
    # Task 3.7: behind Caddy we must trust the proxy so slowapi's
    # key_func=get_remote_address sees the real client IP, not Caddy's
    # container IP (otherwise every user shares one rate-limit bucket).
    # Caddy sets X-Forwarded-For by default; we honor it here.
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        proxy_headers=True,
        forwarded_allow_ips="*",  # trust Caddy in front
    )
