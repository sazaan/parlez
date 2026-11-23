"""
SQLite-backed storage for Parlez.

This module replaces the previous JSON-file storage with SQLite while keeping
the same nested data structures (users, shared links, comments) as JSON columns.
The Storage class is now stateless: every read or write hits the database so
multiple worker processes stay consistent and can be scaled horizontally.
"""

import os
import json
import math
import time
import datetime
import bcrypt
from typing import Optional
from sqlalchemy import create_engine, Column, String, Text, JSON, Integer, Float, text, inspect, Index, func
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def _default_database_url() -> str:
    """Return the default SQLite database URL when DATABASE_URL is not set."""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "parlez.db")
    return f"sqlite:///{db_path}"


def get_database_url() -> str:
    """Return the configured database URL, supporting Postgres/SQLite."""
    url = os.getenv("DATABASE_URL", _default_database_url())
    # Render/Heroku style postgres:// URLs need to be converted for SQLAlchemy.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String(254), nullable=True)
    password_hash = Column(Text, nullable=False)
    data = Column(JSON, nullable=False, default=dict)


# NULL permits pre-email accounts; a unique index also protects concurrent signup.
USER_EMAIL_INDEX = Index("ix_users_email", User.email, unique=True)


class SharedLink(Base):
    __tablename__ = "shared_links"
    id = Column(String, primary_key=True)
    data = Column(JSON, nullable=False, default=dict)


class CommentGroup(Base):
    __tablename__ = "comments"
    conv_id = Column(String, primary_key=True)
    data = Column(JSON, nullable=False, default=list)


class SystemSetting(Base):
    """Persistent runtime settings managed by trusted server-side controls."""
    __tablename__ = "system_settings"
    key = Column(String, primary_key=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(Float, nullable=False)


class AdminAudit(Base):
    """Small, non-sensitive audit trail for privileged administrative actions."""
    __tablename__ = "admin_audit"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    action = Column(String, nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(Float, nullable=False)


class AdminSession(Base):
    """Short-lived server-side admin sessions, revocable on logout."""
    __tablename__ = "admin_sessions"
    id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    expires_at = Column(Float, nullable=False, index=True)


class LlmUsage(Base):
    """Atomic per-user, per-UTC-day LLM request counter.

    Kept in its own typed table instead of the user JSON blob so concurrent
    requests cannot lose updates and failed calls still consume budget.
    """
    __tablename__ = "llm_usage"
    user_id = Column(String, primary_key=True)
    day = Column(String, primary_key=True)
    count = Column(Integer, nullable=False, default=0)
    updated_at = Column(Float, nullable=False)


class RewardEvent(Base):
    """Idempotency record for one learning action."""
    __tablename__ = "reward_events"
    event_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(Float, nullable=False)


class XpLedger(Base):
    """Append-only XP entries; the sum is the authoritative total."""
    __tablename__ = "xp_ledger"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    delta = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    event_id = Column(String, nullable=False, index=True)
    day = Column(String, nullable=False, index=True)
    created_at = Column(Float, nullable=False)


class StreakState(Base):
    __tablename__ = "streak_states"
    user_id = Column(String, primary_key=True)
    current = Column(Integer, nullable=False, default=0)
    best = Column(Integer, nullable=False, default=0)
    last_day = Column(String, nullable=True)
    freezes = Column(Integer, nullable=False, default=2)
    frozen_dates = Column(JSON, nullable=False, default=list)


class UserBadge(Base):
    __tablename__ = "user_badges"
    user_id = Column(String, nullable=False, primary_key=True)
    badge_id = Column(String, primary_key=True)
    earned_at = Column(Float, nullable=False)


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    plan_id = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    amount_npr = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="initiated")
    provider_ref = Column(String, nullable=True)
    checkout_url = Column(Text, nullable=True)
    created_at = Column(Float, nullable=False)
    updated_at = Column(Float, nullable=False)


class Entitlement(Base):
    __tablename__ = "entitlements"
    user_id = Column(String, primary_key=True)
    plan = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    valid_until = Column(Float, nullable=True)
    provider = Column(String, nullable=True)
    provider_ref = Column(String, nullable=True)
    updated_at = Column(Float, nullable=False)


class PaymentEvent(Base):
    """Idempotency inbox for provider callbacks / webhooks."""
    __tablename__ = "payment_events"
    id = Column(String, primary_key=True)
    provider = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(Float, nullable=False)


class Storage:
    """Stateless SQLite-backed storage with the same interface as the old JSON Storage."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or get_database_url()
        self.engine = create_engine(
            self.database_url,
            connect_args={"check_same_thread": False} if self.database_url.startswith("sqlite") else {},
            json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
            json_deserializer=lambda text: json.loads(text) if text else {},
        )
        self._enable_wal()
        Base.metadata.create_all(self.engine)
        self._migrate_user_email()
        self.Session = sessionmaker(bind=self.engine)

    def _migrate_user_email(self):
        """Add nullable email to existing databases without changing legacy accounts.

        Run startup migrations with a single app instance during deployment.
        create_all() alone does not add columns to an existing table.
        """
        if "email" not in {column["name"] for column in inspect(self.engine).get_columns("users")}:
            with self.engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(254)"))
        USER_EMAIL_INDEX.create(self.engine, checkfirst=True)

    def _enable_wal(self):
        """Enable WAL mode for SQLite only."""
        if not self.database_url.startswith("sqlite"):
            return
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))

    @staticmethod
    def _user_from_row(row: User) -> dict:
        data = row.data or {}
        return {"id": row.id, "username": row.username, "password_hash": row.password_hash, **data, "email": row.email}

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def create_user(self, username: str, password_hash: str, name: Optional[str] = None, email: Optional[str] = None) -> dict:
        import uuid
        import time
        user_id = str(uuid.uuid4())[:8]
        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "name": name or username,
            "level": "A1",
            "created_at": time.time(),
            "conversations": {},
            "progress": {
                "xp": 0,
                "streak": 0,
                "best_streak": 0,
                "lessons_completed": [],
                "tests_taken": [],
                "level": "A1",
                "last_active": None,
            },
            "flashcards": {},
            "exercise_history": [],
            "test_results": [],
        }
        data = {k: v for k, v in user.items() if k not in ("id", "username", "password_hash", "email")}
        with self.Session() as session:
            with session.begin():
                session.add(User(id=user_id, username=username, email=email, password_hash=password_hash, data=data))
        return user

    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        with self.Session() as session:
            row = session.query(User).filter_by(id=user_id).first()
            return self._user_from_row(row) if row else None

    def find_user_by_referral_code(self, code: str) -> Optional[dict]:
        """Find the account that owns a referral code (small-scale scan)."""
        with self.Session() as session:
            for row in session.query(User).all():
                if (row.data or {}).get("referral_code") == code:
                    return self._user_from_row(row)
        return None

    def count_referrals(self, code: str) -> int:
        with self.Session() as session:
            return sum(
                1 for row in session.query(User).all()
                if (row.data or {}).get("referred_by") == code
            )

    def get_user_by_username(self, username: str) -> Optional[dict]:
        with self.Session() as session:
            row = session.query(User).filter_by(username=username).first()
            return self._user_from_row(row) if row else None

    def username_exists(self, username: str) -> bool:
        with self.Session() as session:
            return session.query(User.id).filter_by(username=username).first() is not None

    def email_exists(self, email: str) -> bool:
        with self.Session() as session:
            return session.query(User.id).filter_by(email=email).first() is not None

    def count_users(self) -> int:
        with self.Session() as session:
            return session.query(func.count(User.id)).scalar() or 0

    def list_admin_users(self, limit: int = 25, offset: int = 0) -> dict:
        """Return a paginated, privacy-limited directory for authenticated admins."""
        with self.Session() as session:
            total = session.query(func.count(User.id)).scalar() or 0
            rows = (
                session.query(
                    User.username,
                    User.email,
                    User.data["name"].as_string(),
                    User.data["level"].as_string(),
                    User.data["progress"]["level"].as_string(),
                    User.data["created_at"].as_string(),
                    User.data["progress"]["last_active"].as_string(),
                )
                .order_by(User.username.asc())
                .offset(offset)
                .limit(limit)
                .all()
            )

        users = []
        for username, email, name, level, progress_level, raw_registered_at, last_active in rows:
            if not isinstance(name, str) or not name.strip():
                name = username
            if not isinstance(level, str) or not level.strip():
                level = progress_level
            if not isinstance(level, str) or not level.strip():
                level = "A1"
            try:
                registered_at = None if isinstance(raw_registered_at, bool) else float(raw_registered_at)
                if registered_at is not None and (not math.isfinite(registered_at) or registered_at <= 0):
                    registered_at = None
            except (TypeError, ValueError):
                registered_at = None
            if not isinstance(last_active, str) or not last_active.strip():
                last_active = None

            users.append({
                "name": name,
                "username": username,
                "email": email if isinstance(email, str) and email.strip() else None,
                "level": level,
                "registered_at": registered_at,
                "last_active": last_active,
            })

        return {"total": total, "users": users, "limit": limit, "offset": offset}

    def verify_user(self, username: str, password: str) -> Optional[str]:
        user = self.get_user_by_username(username)
        if not user:
            return None
        stored = user.get("password_hash", "").encode("utf-8")
        if bcrypt.checkpw(password.encode("utf-8"), stored):
            return user["id"]
        return None

    def save_user(self, user: dict) -> None:
        user_id = user["id"]
        username = user["username"]
        password_hash = user["password_hash"]
        data = {k: v for k, v in user.items() if k not in ("id", "username", "password_hash", "email")}
        with self.Session() as session:
            with session.begin():
                row = session.query(User).filter_by(id=user_id).first()
                if row:
                    row.username = username
                    row.password_hash = password_hash
                    row.data = data
                else:
                    session.add(User(id=user_id, username=username, email=user.get("email"), password_hash=password_hash, data=data))

    # ------------------------------------------------------------------
    # LLM budget (atomic, UTC-day keyed)
    # ------------------------------------------------------------------

    def consume_llm_budget(self, user_id: str, day: str, limit: int) -> int:
        """Atomically reserve one LLM request for (user, UTC day).

        Returns the new count, or -1 when the daily limit is already reached.
        The whole check-and-increment runs inside one transaction so parallel
        requests cannot both read the same count and overrun the budget.
        """
        with self.Session() as session:
            with session.begin():
                row = session.query(LlmUsage).filter_by(user_id=user_id, day=day).first()
                if row is None:
                    session.add(LlmUsage(user_id=user_id, day=day, count=1, updated_at=time.time()))
                    return 1
                if row.count >= limit:
                    return -1
                row.count += 1
                row.updated_at = time.time()
                return row.count

    # ------------------------------------------------------------------
    # Rewards: idempotent events, append-only XP ledger, streaks, badges
    # ------------------------------------------------------------------

    def award_event(self, user_id, event_type, points, event_id, day, daily_cap, metadata=None):
        """Atomically record a learning event and grant capped XP.

        Returns None when the event was already recorded (idempotent replay),
        otherwise a summary used to keep the legacy progress blob in sync.
        """
        now = time.time()
        with self.Session() as session:
            with session.begin():
                if session.query(RewardEvent).filter_by(event_id=event_id).first():
                    return None
                session.add(RewardEvent(
                    event_id=event_id, user_id=user_id, event_type=event_type,
                    payload=metadata or {}, created_at=now,
                ))

                used = session.query(func.coalesce(func.sum(XpLedger.delta), 0)).filter(
                    XpLedger.user_id == user_id, XpLedger.day == day
                ).scalar() or 0
                granted = max(0, min(int(points), int(daily_cap) - int(used)))
                session.add(XpLedger(
                    user_id=user_id, delta=granted, reason=event_type,
                    event_id=event_id, day=day, created_at=now,
                ))

                streak = session.query(StreakState).filter_by(user_id=user_id).first()
                if streak is None:
                    streak = StreakState(user_id=user_id, current=1, best=1, last_day=day,
                                         freezes=2, frozen_dates=[])
                    session.add(streak)
                elif streak.last_day != day:
                    yesterday = (datetime.date.fromisoformat(day) - datetime.timedelta(days=1)).isoformat()
                    if streak.last_day == yesterday:
                        streak.current += 1
                    elif streak.freezes > 0:
                        streak.freezes -= 1
                        dates = list(streak.frozen_dates or [])
                        dates.append(streak.last_day or day)
                        streak.frozen_dates = dates
                    else:
                        streak.current = 1
                    streak.best = max(streak.best, streak.current)
                    streak.last_day = day

                total = session.query(func.coalesce(func.sum(XpLedger.delta), 0)).filter(
                    XpLedger.user_id == user_id
                ).scalar() or 0
                today_xp = int(used) + granted
                return {
                    "granted": granted,
                    "total_xp": int(total),
                    "today_xp": today_xp,
                    "daily_cap": int(daily_cap),
                    "streak": streak.current,
                    "best_streak": streak.best,
                    "freezes": streak.freezes,
                }

    def award_badge(self, user_id, badge_id):
        with self.Session() as session:
            with session.begin():
                exists = session.query(UserBadge).filter_by(user_id=user_id, badge_id=badge_id).first()
                if exists:
                    return False
                session.add(UserBadge(user_id=user_id, badge_id=badge_id, earned_at=time.time()))
                return True

    def reward_summary(self, user_id, day, limit=20):
        with self.Session() as session:
            streak = session.query(StreakState).filter_by(user_id=user_id).first()
            total = session.query(func.coalesce(func.sum(XpLedger.delta), 0)).filter(
                XpLedger.user_id == user_id
            ).scalar() or 0
            today = session.query(func.coalesce(func.sum(XpLedger.delta), 0)).filter(
                XpLedger.user_id == user_id, XpLedger.day == day
            ).scalar() or 0
            badges = [row.badge_id for row in session.query(UserBadge.badge_id).filter_by(user_id=user_id)]
            events = (
                session.query(XpLedger)
                .filter_by(user_id=user_id)
                .order_by(XpLedger.created_at.desc())
                .limit(limit)
                .all()
            )
        return {
            "total_xp": int(total),
            "today_xp": int(today),
            "streak": streak.current if streak else 0,
            "best_streak": streak.best if streak else 0,
            "freezes": streak.freezes if streak else 2,
            "badges": sorted(badges),
            "ledger": [
                {"reason": e.reason, "delta": e.delta, "day": e.day, "created_at": e.created_at}
                for e in events
            ],
        }

    # ------------------------------------------------------------------
    # Payments and entitlements
    # ------------------------------------------------------------------

    def create_payment_attempt(self, attempt_id, user_id, plan_id, provider, amount_npr, checkout_url=None):
        now = time.time()
        with self.Session() as session:
            with session.begin():
                session.add(PaymentAttempt(
                    id=attempt_id, user_id=user_id, plan_id=plan_id, provider=provider,
                    amount_npr=amount_npr, status="initiated", checkout_url=checkout_url,
                    created_at=now, updated_at=now,
                ))

    def get_payment_attempt(self, attempt_id):
        with self.Session() as session:
            row = session.query(PaymentAttempt).filter_by(id=attempt_id).first()
            return {
                "id": row.id, "user_id": row.user_id, "plan_id": row.plan_id,
                "provider": row.provider, "amount_npr": row.amount_npr,
                "status": row.status, "provider_ref": row.provider_ref,
                "checkout_url": row.checkout_url, "created_at": row.created_at,
            } if row else None

    def set_attempt_provider_ref(self, attempt_id, provider_ref):
        with self.Session() as session:
            with session.begin():
                row = session.query(PaymentAttempt).filter_by(id=attempt_id).first()
                if row:
                    row.provider_ref = provider_ref
                    row.status = "pending"
                    row.updated_at = time.time()

    def mark_attempt_paid(self, attempt_id):
        """Atomic transition pending -> paid. Returns False if already settled."""
        with self.Session() as session:
            with session.begin():
                row = session.query(PaymentAttempt).filter_by(id=attempt_id).first()
                if not row or row.status != "pending":
                    return False
                row.status = "paid"
                row.updated_at = time.time()
                return True

    def claim_payment_event(self, event_id, provider, event_type, payload):
        with self.Session() as session:
            with session.begin():
                if session.query(PaymentEvent).filter_by(id=event_id).first():
                    return False
                session.add(PaymentEvent(
                    id=event_id, provider=provider, event_type=event_type,
                    payload=payload, created_at=time.time(),
                ))
                return True

    def set_entitlement(self, user_id, plan, status, valid_until, provider, provider_ref):
        with self.Session() as session:
            with session.begin():
                row = session.query(Entitlement).filter_by(user_id=user_id).first()
                if row is None:
                    session.add(Entitlement(
                        user_id=user_id, plan=plan, status=status, valid_until=valid_until,
                        provider=provider, provider_ref=provider_ref, updated_at=time.time(),
                    ))
                else:
                    row.plan, row.status, row.valid_until = plan, status, valid_until
                    row.provider, row.provider_ref, row.updated_at = provider, provider_ref, time.time()

    def get_entitlement(self, user_id):
        with self.Session() as session:
            row = session.query(Entitlement).filter_by(user_id=user_id).first()
            if not row:
                return {"plan": "free", "status": "active", "valid_until": None}
            return {
                "plan": row.plan, "status": row.status, "valid_until": row.valid_until,
                "provider": row.provider, "updated_at": row.updated_at,
            }

    # ------------------------------------------------------------------
    # Runtime settings and administrator audit trail
    # ------------------------------------------------------------------

    def get_setting(self, key: str, default=None):
        with self.Session() as session:
            row = session.query(SystemSetting).filter_by(key=key).first()
            return row.value if row else default

    def set_setting(self, key: str, value):
        self.set_settings({key: value})
        return value

    def set_settings(self, settings: dict):
        import time
        updated_at = time.time()
        with self.Session() as session:
            with session.begin():
                for key, value in settings.items():
                    row = session.query(SystemSetting).filter_by(key=key).first()
                    if row:
                        row.value = value
                        row.updated_at = updated_at
                    else:
                        session.add(SystemSetting(key=key, value=value, updated_at=updated_at))

    def delete_setting(self, key: str) -> None:
        with self.Session() as session:
            with session.begin():
                session.query(SystemSetting).filter_by(key=key).delete(synchronize_session=False)

    def create_admin_session(self, session_id: str, username: str, expires_at: float) -> None:
        import time
        with self.Session() as session:
            with session.begin():
                session.query(AdminSession).filter(AdminSession.expires_at <= time.time()).delete(synchronize_session=False)
                session.add(AdminSession(id=session_id, username=username, expires_at=expires_at))

    def admin_session_is_active(self, session_id: str, username: str) -> bool:
        import time
        with self.Session() as session:
            return session.query(AdminSession.id).filter(
                AdminSession.id == session_id,
                AdminSession.username == username,
                AdminSession.expires_at > time.time(),
            ).first() is not None

    def revoke_admin_session(self, session_id: str) -> bool:
        with self.Session() as session:
            with session.begin():
                deleted = session.query(AdminSession).filter_by(id=session_id).delete(synchronize_session=False)
                return bool(deleted)

    def list_admin_sessions(self) -> list[dict]:
        with self.Session() as session:
            rows = session.query(AdminSession).order_by(AdminSession.expires_at.desc()).all()
            return [
                {"id": row.id, "username": row.username, "expires_at": row.expires_at}
                for row in rows
            ]

    def revoke_all_admin_sessions(self, username: str) -> None:
        """Revoke all active admin sessions after an authentication-factor change."""
        with self.Session() as session:
            with session.begin():
                session.query(AdminSession).filter_by(username=username).delete(synchronize_session=False)

    def add_admin_audit(self, username: str, action: str, details: Optional[dict] = None):
        import time
        with self.Session() as session:
            with session.begin():
                session.add(AdminAudit(
                    username=username,
                    action=action,
                    details=details or {},
                    created_at=time.time(),
                ))
                stale_ids = [
                    row[0]
                    for row in session.query(AdminAudit.id)
                    .order_by(AdminAudit.id.desc())
                    .offset(1000)
                    .all()
                ]
                if stale_ids:
                    session.query(AdminAudit).filter(AdminAudit.id.in_(stale_ids)).delete(synchronize_session=False)
        # Keep logs useful without duplicating admin usernames or sensitive audit details.
        from observability import log_event
        log_event("admin.audit.recorded", action=action, actor_type="admin")

    def list_admin_audit(self, limit: int = 100) -> list[dict]:
        bounded_limit = max(1, min(int(limit), 200))
        with self.Session() as session:
            rows = (
                session.query(AdminAudit)
                .order_by(AdminAudit.id.desc())
                .limit(bounded_limit)
                .all()
            )
            return [
                {
                    "id": row.id,
                    "username": row.username,
                    "action": row.action,
                    "details": row.details or {},
                    "created_at": row.created_at,
                }
                for row in rows
            ]

    # ------------------------------------------------------------------
    # Shared links
    # ------------------------------------------------------------------

    def create_shared(self, share_id: str, data: dict) -> dict:
        with self.Session() as session:
            with session.begin():
                session.add(SharedLink(id=share_id, data=data))
        return data

    def get_shared(self, share_id: str) -> Optional[dict]:
        with self.Session() as session:
            row = session.query(SharedLink).filter_by(id=share_id).first()
            if row and row.data:
                return {**row.data, "id": row.id}
            return None

    def list_shared_by_user(self, user_id: str) -> list:
        with self.Session() as session:
            rows = session.query(SharedLink).all()
            return [
                {**row.data, "id": row.id}
                for row in rows
                if row.data and row.data.get("user_id") == user_id
            ]

    def delete_shared(self, share_id: str) -> bool:
        with self.Session() as session:
            with session.begin():
                row = session.query(SharedLink).filter_by(id=share_id).first()
                if row:
                    session.delete(row)
                    return True
                return False

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    def get_comments(self, conv_id: str) -> list:
        with self.Session() as session:
            row = session.query(CommentGroup).filter_by(conv_id=conv_id).first()
            return list(row.data) if row and row.data else []

    def _upsert_comment_group(self, session, conv_id: str, comments: list) -> None:
        row = session.query(CommentGroup).filter_by(conv_id=conv_id).first()
        if row:
            row.data = comments
        else:
            session.add(CommentGroup(conv_id=conv_id, data=comments))

    def add_comment(self, conv_id: str, comment: dict) -> dict:
        with self.Session() as session:
            with session.begin():
                row = session.query(CommentGroup).filter_by(conv_id=conv_id).first()
                comments = list(row.data) if row and row.data else []
                comments.append(comment)
                self._upsert_comment_group(session, conv_id, comments)
        return comment

    def delete_comment(self, conv_id: str, comment_id: str) -> bool:
        with self.Session() as session:
            with session.begin():
                row = session.query(CommentGroup).filter_by(conv_id=conv_id).first()
                if not row or not row.data:
                    return False
                comments = [c for c in row.data if c.get("id") != comment_id]
                if len(comments) == len(row.data):
                    return False
                self._upsert_comment_group(session, conv_id, comments)
                return True

    def set_comments(self, conv_id: str, comments: list):
        """Replace all comments for a conversation (used by migration)."""
        with self.Session() as session:
            with session.begin():
                self._upsert_comment_group(session, conv_id, list(comments))

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self):
        self.engine.dispose()
