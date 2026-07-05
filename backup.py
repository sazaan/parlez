#!/usr/bin/env python3
"""
Automated SQLite backup for Parlez.

Creates a timestamped backup of data/parlez.db using SQLite's online backup,
which is safe to run while the application is running.

Usage:
    python3 backup.py                    # keep last 7 backups
    python3 backup.py --keep 30          # keep last 30 backups
    python3 backup.py --dest /backups    # backup destination directory
"""

import os
import sys
import shutil
import sqlite3
import argparse
from datetime import datetime, timezone

import db


def _sqlite_path(storage: db.Storage) -> str:
    """Return the filesystem path for a SQLite database URL."""
    url = storage.database_url
    if not url.startswith("sqlite:///"):
        raise RuntimeError(f"Backup only supports SQLite databases, got: {url}")
    return url[len("sqlite:///"):]


def backup_database(dest_dir: str, keep: int):
    os.makedirs(dest_dir, exist_ok=True)

    storage = db.Storage()
    db_path = _sqlite_path(storage)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"parlez_{timestamp}.db"
    backup_path = os.path.join(dest_dir, backup_name)

    # Use SQLite's online backup for a consistent snapshot.
    source = sqlite3.connect(db_path)
    try:
        dest = sqlite3.connect(backup_path)
        try:
            with dest:
                source.backup(dest)
        finally:
            dest.close()
    finally:
        source.close()

    # Copy WAL files if they exist (WAL mode is enabled).
    for suffix in ("-wal", "-shm"):
        src = db_path + suffix
        if os.path.exists(src):
            shutil.copy2(src, backup_path + suffix)

    # Remove old backups.
    backups = sorted(
        [f for f in os.listdir(dest_dir) if f.startswith("parlez_") and f.endswith(".db")],
        key=lambda f: os.path.getctime(os.path.join(dest_dir, f)),
    )
    for old in backups[:-keep]:
        old_path = os.path.join(dest_dir, old)
        os.remove(old_path)
        for suffix in ("-wal", "-shm"):
            wal_path = old_path + suffix
            if os.path.exists(wal_path):
                os.remove(wal_path)
        print(f"Removed old backup: {old}")

    print(f"Backup created: {backup_path}")
    storage.close()
    return backup_path


def main():
    parser = argparse.ArgumentParser(description="Backup Parlez SQLite database")
    parser.add_argument("--dest", default="data/backups", help="Backup destination directory")
    parser.add_argument("--keep", type=int, default=7, help="Number of backups to keep")
    args = parser.parse_args()

    storage = db.Storage()
    db_path = _sqlite_path(storage)
    storage.close()

    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    backup_database(args.dest, args.keep)


if __name__ == "__main__":
    main()
