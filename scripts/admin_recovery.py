#!/usr/bin/env python3
"""Emergency admin MFA recovery — server-side only.

If ADMIN_SESSION_SECRET was rotated while MFA was enabled, the encrypted TOTP
secret can no longer be decrypted and the admin console fails closed (503).
This script clears the stored MFA state after an explicit typed confirmation so
an operator can sign in with password alone and re-enrol MFA.

Usage:  python scripts/admin_recovery.py --confirm RESET-MFA
        python scripts/admin_recovery.py --status
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import Storage  # noqa: E402

MFA_KEYS = ("admin_mfa", "admin_mfa_pending")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", action="store_true", help="Show whether MFA state is present")
    parser.add_argument("--confirm", metavar="TOKEN", help="Type RESET-MFA to clear MFA state")
    args = parser.parse_args()

    storage = Storage()
    if args.status or not args.confirm:
        for key in MFA_KEYS:
            print(f"{key}: {'present' if storage.get_setting(key) is not None else 'empty'}")
        if not args.confirm:
            print("Pass --confirm RESET-MFA to clear both keys.")
        return 0

    if args.confirm != "RESET-MFA":
        print("Confirmation token mismatch. Nothing was changed.", file=sys.stderr)
        return 2

    for key in MFA_KEYS:
        storage.delete_setting(key)
    storage.revoke_all_admin_sessions(os.getenv("ADMIN_USERNAME", ""))
    storage.add_admin_audit("recovery", "admin_mfa_reset", {"keys": list(MFA_KEYS)})
    print("MFA state cleared and admin sessions revoked. Sign in with password and re-enrol MFA.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
