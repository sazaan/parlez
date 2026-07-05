#!/usr/bin/env python3
"""
Migrate legacy JSON data files into SQLite.

Reads:
  data/users.json
  data/shared.json
  data/comments.json

Writes:
  data/parlez.db

Safe to run multiple times: existing SQLite rows are updated, not duplicated.
"""

import json
import os
import time
import uuid
import db

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_json(name, default):
    path = os.path.join(DATA_DIR, name)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: could not load {name}: {e}")
    return default


def _default_user(uid: str, username: str, password_hash: str, source: dict) -> dict:
    """Build a complete user dict from legacy JSON data."""
    now = time.time()
    return {
        "id": source.get("id", uid),
        "username": username,
        "password_hash": password_hash,
        "name": source.get("name", username),
        "level": source.get("level", "A1"),
        "created_at": source.get("created_at", now),
        "conversations": source.get("conversations", {}),
        "progress": source.get("progress", {
            "xp": 0,
            "streak": 0,
            "best_streak": 0,
            "lessons_completed": [],
            "tests_taken": [],
            "level": source.get("level", "A1"),
            "last_active": None,
        }),
        "flashcards": source.get("flashcards", {}),
        "exercise_history": source.get("exercise_history", []),
        "test_results": source.get("test_results", []),
    }


def migrate():
    storage = db.Storage()

    users = load_json("users.json", {})
    shared = load_json("shared.json", {})
    comments = load_json("comments.json", {})

    migrated_users = 0
    for uid, user in users.items():
        if "username" not in user or "password_hash" not in user:
            print(f"Skipping user {uid}: missing username or password_hash")
            continue
        storage.save_user(_default_user(uid, user["username"], user["password_hash"], user))
        migrated_users += 1

    for sid, data in shared.items():
        storage.create_shared(sid, data)

    for cid, data in comments.items():
        # Ensure comment group data is a list.
        if not isinstance(data, list):
            data = []
        # Backfill missing ids to keep the API consistent.
        for comment in data:
            if "id" not in comment:
                comment["id"] = str(uuid.uuid4())[:8]
        storage.set_comments(cid, data)

    print(f"Migrated {migrated_users} users, {len(shared)} shared links, {len(comments)} comment groups")
    print(f"Database URL: {storage.database_url}")


if __name__ == "__main__":
    migrate()
