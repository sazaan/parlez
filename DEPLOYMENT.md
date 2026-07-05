# Parlez Deployment Guide

## Environment variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Required:

| Variable | Description |
|----------|-------------|
| `NVIDIA_API_KEY` | Your NVIDIA NIM API key from https://build.nvidia.com/ |
| `JWT_SECRET` | At least 32 characters. Generate with `openssl rand -hex 32` |

Optional:

| Variable | Default | Description |
|----------|---------|-------------|
| `TOKEN_EXPIRY_HOURS` | `24` | JWT token lifetime |
| `COOKIE_SECURE` | `true` | Set to `false` for local HTTP dev only |
| `COOKIE_SAMESITE` | `lax` | Cookie SameSite attribute |
| `REDIS_URL` | unset | Redis URI for shared rate-limit storage. Required for serverless/multi-instance deployments (e.g. Vercel). |

## Local development

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements-dev.txt
JWT_SECRET=$(openssl rand -hex 32) NVIDIA_API_KEY=dummy venv/bin/python main.py
```

Visit http://localhost:8000.

## Production deployment

### 1. Migrate existing data (if upgrading from JSON files)

```bash
python3 migrate_to_sqlite.py
```

This reads `data/users.json`, `data/shared.json`, and `data/comments.json` and writes them to `data/parlez.db`.

### 2. Deploy with Docker Compose and HTTPS

Set your public domain:

```bash
export PARLEZ_HOST=parlez.example.com
```

Point that DNS record to your server, then run:

```bash
docker compose -f docker-compose.prod.yml up -d
```

Caddy will automatically obtain a Let's Encrypt certificate.

### 3. Backups

Run a manual backup:

```bash
python3 backup.py
```

Schedule automated nightly backups with cron:

```cron
0 3 * * * cd /path/to/parlez && /path/to/parlez/venv/bin/python backup.py --keep 30 >> /var/log/parlez-backup.log 2>&1
```

Backups are stored in `data/backups/` by default.

### 4. Upgrades

```bash
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

Before major upgrades, run `python3 backup.py`.

## Security checklist

- [ ] `.env` is not committed and has strong `JWT_SECRET`
- [ ] `COOKIE_SECURE=true` in production
- [ ] App served over HTTPS
- [ ] `data/` directory is backed up regularly
- [ ] `NVIDIA_API_KEY` rotated if ever exposed
- [ ] `REDIS_URL` configured for serverless/multi-instance deployments so rate limits are shared across instances

## Serverless / Vercel deployments

On serverless platforms each function instance has its own memory, so `slowapi`'s default in-memory rate limiting does not share counters between instances. Set `REDIS_URL` (e.g. Vercel KV, Upstash Redis, or any Redis-compatible provider) to enforce global rate limits.

## CI/CD

The included `.github/workflows/ci.yml` runs on every push and PR:

- `ruff check`
- Python syntax check
- `pytest`
- TruffleHog secret scan
