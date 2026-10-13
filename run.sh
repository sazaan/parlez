#!/usr/bin/env bash

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
umask 077

# Learning Chatbot - Docker Quick Start

echo "📚 Parlez - Docker Quick Start"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo ""
    echo "Install Docker:"
    echo "  Ubuntu/Debian: sudo apt install docker.io"
    echo "  Or visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Use the same Compose implementation for detection, build, and startup.
if docker compose version &> /dev/null; then
    COMPOSE=(docker compose)
elif command -v docker-compose &> /dev/null; then
    COMPOSE=(docker-compose)
else
    echo "❌ Docker Compose is not installed."
    echo ""
    echo "Install Docker Compose:"
    echo "  sudo apt install docker-compose"
    echo "  Or visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create a private .env on first run. Admin credentials are generated below.
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found; creating it from .env.example."
    cp .env.example .env
fi
chmod 600 .env

admin_credentials_complete=true
for key in ADMIN_USERNAME ADMIN_PASSWORD_HASH ADMIN_TOTP_SECRET ADMIN_SESSION_SECRET; do
    if ! grep -Eq "^${key}=[[:space:]]*[^[:space:]]" .env; then
        admin_credentials_complete=false
        break
    fi
done

if [ "$admin_credentials_complete" = false ] && { [ ! -t 0 ] || [ ! -t 1 ]; }; then
    echo "❌ Admin credentials are missing and must be generated interactively."
    echo "Run ./run.sh from a terminal, or generate them manually with:"
    echo "  python scripts/generate_admin_credentials.py --env-file .env"
    exit 1
fi

echo "🐳 Building the application image..."
"${COMPOSE[@]}" build chatbot

if [ "$admin_credentials_complete" = false ]; then
    echo ""
    echo "🔐 Admin credentials are not configured. The setup will ask you to choose an admin username and password."
    echo "The generated password hash, TOTP secret, and session key will be written directly to .env."
    echo "An authenticator enrollment URI will be shown once; add it to your authenticator app and keep it private."
    echo ""
    HOST_UID="$(id -u)"
    HOST_GID="$(id -g)"
    "${COMPOSE[@]}" run --rm --no-deps \
        --user "${HOST_UID}:${HOST_GID}" \
        -v "${PWD}:/workspace" \
        chatbot \
        python /app/scripts/generate_admin_credentials.py --env-file /workspace/.env
fi

# Require at least one configured hosted provider key. The admin console can
# switch between NVIDIA, Gemini, OpenRouter, and OpenCode Zen.
env_value() {
    local key="$1" value first_char last_char
    value="$(awk -F= -v key="$key" '$1 == key { value = substr($0, index($0, "=") + 1) } END { print value }' .env)"
    if [ "${#value}" -ge 2 ]; then
        first_char="${value:0:1}"
        last_char="${value: -1}"
        if [ "$first_char" = "$last_char" ] && { [ "$first_char" = '"' ] || [ "$first_char" = "'" ]; }; then
            value="${value:1:${#value}-2}"
        fi
    fi
    printf '%s' "$value"
}

has_provider_key=false
for key in NVIDIA_API_KEY GEMINI_API_KEY OPENROUTER_API_KEY OPENCODE_ZEN_API_KEY OPENCODE_API_KEY; do
    value="$(env_value "$key")"
    value_nonspace="${value//[[:space:]]/}"
    case "$value_nonspace" in
        ""|your-*|change-me*|\#*) ;;
        *) has_provider_key=true; break ;;
    esac
done
if [ "$has_provider_key" = false ]; then
    echo "⚠️  Add at least one supported AI provider API key to .env before starting Parlez."
    echo ""
    echo "Supported keys: NVIDIA_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY, or OPENCODE_ZEN_API_KEY."
    echo "Edit .env, then run ./run.sh again:"
    echo "  nano .env"
    echo ""
    exit 1
fi

echo ""
echo "🚀 Starting Parlez in the background..."
echo "📖 Open http://localhost:8000 in your browser"
BOOTSTRAP_PROVIDER="$(env_value AI_PROVIDER)"
BOOTSTRAP_PROVIDER="${BOOTSTRAP_PROVIDER:-nvidia}"
case "$BOOTSTRAP_PROVIDER" in
    gemini) MODEL_ID="$(env_value GEMINI_MODEL)"; MODEL_ID="${MODEL_ID:-gemini-3.8-flash}" ;;
    openrouter) MODEL_ID="$(env_value OPENROUTER_MODEL)"; MODEL_ID="${MODEL_ID:-openrouter/free}" ;;
    opencode_zen) MODEL_ID="$(env_value OPENCODE_ZEN_MODEL)"; MODEL_ID="${MODEL_ID:-big-pickle}" ;;
    *) BOOTSTRAP_PROVIDER=nvidia; MODEL_ID="$(env_value NVIDIA_MODEL)"; MODEL_ID="${MODEL_ID:-nvidia/nemotron-3.5-lightning-30b-a3b}" ;;
esac
echo "🤖 Bootstrap provider/model: ${BOOTSTRAP_PROVIDER} · ${MODEL_ID}"
ADMIN_PATH_VALUE="$(env_value ADMIN_PATH)"
ADMIN_PATH_VALUE="${ADMIN_PATH_VALUE:-/parlez-admin}"
echo "🔐 Admin console: http://localhost:8000${ADMIN_PATH_VALUE}"
echo "📋 Follow logs: ${COMPOSE[*]} logs -f chatbot"
echo "🛑 Stop services: ${COMPOSE[*]} down"
echo ""

"${COMPOSE[@]}" up -d
