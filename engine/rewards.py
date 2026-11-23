"""Server-side reward rules for Parlez.

Only learning behaviours earn points; the client never supplies XP amounts.
All state lives in typed tables (see db.py) and the sum of `xp_ledger` is the
authoritative total. The legacy `progress` blob is kept in sync for older
clients but is no longer trusted.
"""

from __future__ import annotations

import datetime
import uuid

# Points per event. Deliberately modest for repeated actions so streaks and
# meaningful tasks dominate over point farming.
RULES = {
    "chat_message": 5,
    "exercise_correct": 10,
    "lesson_complete": 50,
    "flashcard_review": 5,
    "exam_question_correct": 5,
    "writing_correction": 15,
}

DAILY_XP_CAP = 300

# Badges are informational milestones, never proficiency credentials.
BADGES = {
    "first_steps": "Completed a first learning action",
    "streak_7": "Practised seven days in a row",
    "century": "Earned 100 XP",
    "first_conversation": "Completed a first AI conversation exchange",
}


def utc_day() -> str:
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def award(storage, user, event_type: str, *, metadata=None, event_id=None, multiplier: int = 1) -> dict:
    """Record a learning event and return the updated reward summary.

    `event_id` should be a stable value for retryable client actions (for
    example a lesson id + attempt id). Replaying the same id is a no-op.
    """
    if event_type not in RULES:
        raise ValueError(f"Unknown reward event: {event_type}")
    identifier = event_id or f"{event_type}:{user['id']}:{uuid.uuid4().hex}"
    result = storage.award_event(
        user_id=user["id"],
        event_type=event_type,
        points=RULES[event_type] * max(1, int(multiplier)),
        event_id=identifier,
        day=utc_day(),
        daily_cap=DAILY_XP_CAP,
        metadata=metadata,
    )

    progress = user.setdefault("progress", {"xp": 0, "streak": 0, "best_streak": 0, "last_active": None})
    if result is None:
        # Idempotent replay: refresh from the ledger without granting again.
        summary = storage.reward_summary(user["id"], utc_day(), limit=1)
        result = {key: summary[key] for key in ("total_xp", "today_xp", "streak", "best_streak", "freezes")}
        result["granted"] = 0
        result["daily_cap"] = DAILY_XP_CAP
    else:
        progress["last_active"] = utc_day()

    progress["xp"] = result["total_xp"]
    progress["streak"] = result["streak"]
    progress["best_streak"] = result["best_streak"]

    _maybe_award_badges(storage, user, result)
    return result


def _maybe_award_badges(storage, user, result):
    summary = storage.reward_summary(user["id"], utc_day(), limit=20)
    earned = set(summary["badges"])
    candidates = []
    if result["total_xp"] >= RULES["chat_message"]:
        candidates.append("first_steps")
    if result["total_xp"] >= 100:
        candidates.append("century")
    if result["streak"] >= 7:
        candidates.append("streak_7")
    if any(item["reason"] == "chat_message" for item in summary["ledger"]):
        candidates.append("first_conversation")
    for badge in candidates:
        if badge not in earned:
            storage.award_badge(user["id"], badge)
