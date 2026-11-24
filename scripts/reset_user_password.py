#!/usr/bin/env python3
"""Reset a learner password by username or email (server-side, local use).

Usage: python scripts/reset_user_password.py --identifier sajan --password 'new-password'
       Identifiers and passwords are never logged.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt  # noqa: E402
from db import Storage  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identifier", required=True, help="username or email")
    parser.add_argument("--password", required=True, help="new password (min 8 chars)")
    args = parser.parse_args()

    if len(args.password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        return 2

    storage = Storage()
    user = storage.get_user_by_login(args.identifier)
    if not user:
        print("No account with that username or email.", file=sys.stderr)
        return 1

    user["password_hash"] = bcrypt.hashpw(
        args.password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    storage.save_user(user)
    print(f"Password updated for {user['username']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
