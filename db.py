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

    def revoke_admin_session(self, session_id: str) -> None:
        with self.Session() as session:
            with session.begin():
                session.query(AdminSession).filter_by(id=session_id).delete(synchronize_session=False)

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
