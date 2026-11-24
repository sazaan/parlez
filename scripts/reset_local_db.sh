#!/usr/bin/env bash
# Reset the LOCAL SQLite database used by docker-compose.
#
# IMPORTANT: docker-compose.yml uses a BIND MOUNT (./data:/app/data), so
# `docker compose down -v` does NOT delete data/parlez.db. This script does.
# It refuses to run unless RESET-DB is typed explicitly.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "${1:-}" != "RESET-DB" ]]; then
  echo "This deletes ./data/parlez.db and its WAL/SHM files permanently."
  echo "Usage: bash scripts/reset_local_db.sh RESET-DB"
  exit 1
fi

docker compose down -v 2>/dev/null || true
rm -f data/parlez.db data/parlez.db-wal data/parlez.db-shm
echo "Local database removed. Start the app again to create a fresh one."
