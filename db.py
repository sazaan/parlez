"""
SQLite-backed storage for Parlez.

This module replaces the previous JSON-file storage with SQLite while keeping
the same nested data structures (users, shared links, comments) as JSON columns.
The Storage class is now stateless: every read or write hits the database so
multiple worker processes stay consistent and can be scaled horizontally.
"""

import os
import json
import bcrypt
from typing import Optional
from sqlalchemy import create_engine, Column, String, Text, JSON, text
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
    password_hash = Column(Text, nullable=False)
    data = Column(JSON, nullable=False, default=dict)


class SharedLink(Base):
    __tablename__ = "shared_links"
    id = Column(String, primary_key=True)
    data = Column(JSON, nullable=False, default=dict)


class CommentGroup(Base):
    __tablename__ = "comments"
    conv_id = Column(String, primary_key=True)
    data = Column(JSON, nullable=False, default=list)


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
        self.Session = sessionmaker(bind=self.engine)

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
        return {"id": row.id, "username": row.username, "password_hash": row.password_hash, **data}

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def create_user(self, username: str, password_hash: str, name: Optional[str] = None) -> dict:
        import uuid
        import time
        user_id = str(uuid.uuid4())[:8]
        user = {
            "id": user_id,
            "username": username,
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
        data = {k: v for k, v in user.items() if k not in ("id", "username", "password_hash")}
        with self.Session() as session:
            with session.begin():
                session.add(User(id=user_id, username=username, password_hash=password_hash, data=data))
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
        data = {k: v for k, v in user.items() if k not in ("id", "username", "password_hash")}
        with self.Session() as session:
            with session.begin():
                row = session.query(User).filter_by(id=user_id).first()
                if row:
                    row.username = username
                    row.password_hash = password_hash
                    row.data = data
                else:
                    session.add(User(id=user_id, username=username, password_hash=password_hash, data=data))

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
