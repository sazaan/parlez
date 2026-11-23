"""Reward engine: idempotency, caps, streaks and badges."""

import datetime

import main
from db import StreakState
from engine.rewards import DAILY_XP_CAP, RULES, award, utc_day


def _user():
    return {"id": "reward-user", "progress": {"xp": 0, "streak": 0, "best_streak": 0}}


def test_award_updates_ledger_and_progress():
    user = _user()
    result = award(main.storage, user, "lesson_complete", event_id="lesson-1")

    assert result["granted"] == RULES["lesson_complete"]
    assert result["total_xp"] == RULES["lesson_complete"]
    assert user["progress"]["xp"] == result["total_xp"]
    assert user["progress"]["streak"] == 1


def test_same_event_id_is_idempotent():
    user = _user()
    award(main.storage, user, "exercise_correct", event_id="attempt-1")
    second = award(main.storage, user, "exercise_correct", event_id="attempt-1")

    assert second["granted"] == 0
    assert second["total_xp"] == RULES["exercise_correct"]


def test_daily_cap_is_enforced():
    user = _user()
    for index in range(40):
        award(main.storage, user, "lesson_complete", event_id=f"lesson-{index}")

    summary = main.storage.reward_summary(user["id"], utc_day(), limit=1)
    assert summary["today_xp"] == DAILY_XP_CAP
    assert summary["total_xp"] == DAILY_XP_CAP


def test_streak_uses_a_freeze_for_a_missed_day():
    user = _user()
    today = datetime.date.today()
    yesterday = (today - datetime.timedelta(days=1)).isoformat()
    main.storage.award_event(user["id"], "chat_message", 5, "seed-1", yesterday, DAILY_XP_CAP)
    with main.storage.Session() as session:
        with session.begin():
            state = session.query(StreakState).filter_by(user_id=user["id"]).one()
            state.last_day = (today - datetime.timedelta(days=3)).isoformat()

    award(main.storage, user, "chat_message", event_id="after-gap")

    with main.storage.Session() as session:
        state = session.query(StreakState).filter_by(user_id=user["id"]).one()
    assert state.freezes == 1
    assert state.current == 1


def test_reward_summary_endpoint(auth_client):
    user = main.storage.get_user_by_username("testuser")
    award(main.storage, user, "chat_message", event_id="ep-1")
    r = auth_client.get("/api/rewards/summary")

    assert r.status_code == 200
    data = r.json()
    assert data["total_xp"] == RULES["chat_message"]
    assert data["dailyCap"] == DAILY_XP_CAP
    assert any(badge["id"] == "first_steps" for badge in data["badgeDefinitions"])
