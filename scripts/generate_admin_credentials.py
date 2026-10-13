#!/usr/bin/env python3
"""Generate environment values for Parlez's dedicated admin login.

Run locally (never inside a public web endpoint):
    python scripts/generate_admin_credentials.py

The output contains secrets. Paste it only into the server's ignored .env or
an approved secrets manager; do not commit or share it.
"""

import getpass
import secrets

import bcrypt
import pyotp


def main() -> None:
    username = input("Admin username [parlez-admin]: ").strip() or "parlez-admin"
    if len(username) > 80 or any(ord(char) < 32 for char in username):
        raise SystemExit("Use a username of at most 80 printable characters.")

    password = getpass.getpass("Admin password (at least 16 characters): ")
    if len(password) < 16:
        raise SystemExit("Use a password of at least 16 characters.")
    if len(password.encode("utf-8")) > 72:
        raise SystemExit("bcrypt passwords must be at most 72 bytes; choose a shorter password.")
    confirmation = getpass.getpass("Confirm admin password: ")
    if not secrets.compare_digest(password, confirmation):
        raise SystemExit("Passwords did not match.")

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")
    totp_secret = pyotp.random_base32()
    session_secret = secrets.token_urlsafe(48)
    totp_uri = pyotp.TOTP(totp_secret).provisioning_uri(name=username, issuer_name="Parlez Admin")

    print("\nAdd these values to the backend .env (never to frontend code):\n")
    print(f"ADMIN_USERNAME={username}")
    print(f"ADMIN_PASSWORD_HASH={password_hash}")
    print(f"ADMIN_TOTP_SECRET={totp_secret}")
    print(f"ADMIN_SESSION_SECRET={session_secret}")
    print("ADMIN_SESSION_TTL_MINUTES=15")
    print("\nEnroll this TOTP URI in your authenticator app (the URI contains the TOTP secret):")
    print(totp_uri)
    print("\nKeep the .env file private and restart Parlez after updating it.")


if __name__ == "__main__":
    main()
