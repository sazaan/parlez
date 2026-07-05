# Parlez — Vercel + Supabase + Redis Deployment Guide

This guide walks through deploying the Parlez French-learning chatbot to **Vercel** with **Supabase Postgres** for persistence and **Vercel KV** (Redis) for shared rate limiting.

Keep this document as a reference for rebuilds, team handoffs, and disaster recovery.

---

## Table of contents

1. [Architecture overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Step 1 — Rotate all secrets](#step-1--rotate-all-secrets)
4. [Step 2 — Supabase database](#step-2--supabase-database)
5. [Step 3 — NVIDIA NIM API key](#step-3--nvidia-nim-api-key)
6. [Step 4 — Vercel KV (Redis)](#step-4--vercel-kv-redis)
7. [Step 5 — Vercel project setup](#step-5--vercel-project-setup)
8. [Step 6 — Environment variables](#step-6--environment-variables)
9. [Step 7 — Deploy](#step-7--deploy)
10. [Step 8 — Post-deploy verification](#step-8--post-deploy-verification)
11. [Security checklist](#security-checklist)
12. [Monitoring & maintenance](#monitoring--maintenance)
13. [Troubleshooting](#troubleshooting)
14. [Rollback procedure](#rollback-procedure)

---

## Architecture overview

```
User
  │ HTTPS
  ▼
Vercel Edge / Serverless Functions  ←  REDIS_URL (Vercel KV)
  │                                  ←  shared rate-limit counters
  ▼
FastAPI app (main.py)
  │
  ├───► NVIDIA NIM API  (AI responses)
  │
  └───► Supabase Postgres  (users, conversations, comments, shares)
```

| Service | Purpose | Why |
|---|---|---|
| **Vercel** | Hosting / serverless functions | HTTPS, automatic scaling, easy git deploys |
| **Supabase Postgres** | Persistent database | Replaces local SQLite; shared across instances |
| **Vercel KV** | Redis-compatible store | Shared rate-limit counters across serverless instances |
| **NVIDIA NIM** | LLM API | Powers the French tutor responses |

---

## Prerequisites

- A Git repository with the Parlez code pushed to GitHub/GitLab/Bitbucket.
- A Vercel account: https://vercel.com
- A Supabase account: https://supabase.com
- An NVIDIA account: https://build.nvidia.com
- The Vercel CLI installed locally (optional but useful):
  ```bash
  npm i -g vercel
  ```

---

## Step 1 — Rotate all secrets

**Do this first.** The `.env` file in your repo currently contains a real `NVIDIA_API_KEY` and a weak `JWT_SECRET`.

1. Open `.env` and note the current `NVIDIA_API_KEY` value.
2. Go to https://build.nvidia.com/ → API Keys → revoke the old key.
3. Generate a new NVIDIA API key.
4. Generate a strong JWT secret:
   ```bash
   openssl rand -hex 32
   ```
5. Update your local `.env` with the new values **only for local testing**:
   ```bash
   NVIDIA_API_KEY=nvapi-YOUR-NEW-KEY
   JWT_SECRET=YOUR-NEW-64-CHAR-HEX-SECRET
   ```
6. **Do not commit `.env`.** It is already in `.gitignore`.

---

## Step 2 — Supabase database

Vercel functions are stateless, so SQLite will not work in production. Use Supabase Postgres.

1. Create a new Supabase project.
2. Go to **Project Settings → Database**.
3. Copy the **connection string** (URI). It looks like:
   ```text
   postgresql://postgres:<password>@db.abcdefgh12345678.supabase.co:5432/postgres
   ```
4. In your local `.env`, set:
   ```bash
   DATABASE_URL=postgresql://postgres:<password>@db.abcdefgh12345678.supabase.co:5432/postgres
   ```
5. Run the app locally once to let SQLAlchemy create the tables:
   ```bash
   JWT_SECRET=$(openssl rand -hex 32) NVIDIA_API_KEY=dummy DATABASE_URL=postgresql://... venv/bin/python main.py
   ```
   Then stop it. Tables `users`, `shared_links`, and `comments` should now exist in Supabase.
6. If you have existing SQLite data to migrate, see [Migrate SQLite to Supabase](#migrate-sqlite-to-supabase) at the end of this guide.

---

## Step 3 — NVIDIA NIM API key

1. Go to https://build.nvidia.com/.
2. Sign in or create an account.
3. Navigate to **API Keys**.
4. Click **Generate API Key**.
5. Copy the key. You will add it to Vercel in Step 6.

---

## Step 4 — Vercel KV (Redis)

1. In the Vercel dashboard, go to **Storage → Create → KV**.
2. Choose a name, e.g. `parlez-kv`.
3. Select the region closest to your users.
4. Click **Create**.
5. After creation, Vercel shows environment variables like:
   - `KV_URL`
   - `KV_REST_API_URL`
   - `KV_REST_API_TOKEN`
   - `KV_REST_API_READ_ONLY_TOKEN`
6. Click **Connect Project** (or manually copy the values for Step 6).
7. The Redis URL you need is the value of `KV_URL`. It looks like:
   ```text
   redis://default:xxxxxxxx@some-host.kv.vercel-storage.com:6379
   ```

---

## Step 5 — Vercel project setup

### Option A: Vercel dashboard (recommended for first deploy)

1. Go to https://vercel.com/new.
2. Import the Git repository containing Parlez.
3. Vercel auto-detects Python/FastAPI settings.
4. In the project settings:
   - **Framework Preset**: Other
   - **Build Command**: leave empty
   - **Output Directory**: leave empty
   - **Install Command**: leave empty or use `pip install -r requirements.txt`
   - **Root Directory**: `./` (default)
5. Click **Deploy**.

### Option B: Vercel CLI

```bash
vercel login
vercel --prod
```

---

## Step 6 — Environment variables

In the Vercel dashboard, go to **Project Settings → Environment Variables** and add these:

| Variable | Value | Environment |
|---|---|---|
| `NVIDIA_API_KEY` | `nvapi-...` your new key | Production, Preview |
| `JWT_SECRET` | 64-char hex from `openssl rand -hex 32` | Production, Preview |
| `DATABASE_URL` | Supabase Postgres URI | Production, Preview |
| `REDIS_URL` | Value of `KV_URL` from Vercel KV | Production, Preview |
| `COOKIE_SECURE` | `true` | Production, Preview |
| `COOKIE_SAMESITE` | `lax` | Production, Preview |
| `TOKEN_EXPIRY_HOURS` | `24` | Production, Preview |

### Important notes

- **Never** add `.env` to version control. Vercel env vars are the source of truth in production.
- If you use the Vercel KV **Connect Project** button, `KV_URL` is already set. You can either:
  - Set `REDIS_URL` to `${KV_URL}` (Vercel supports referencing other env vars), or
  - Copy the actual `KV_URL` value into `REDIS_URL`.
- For local development, keep using `.env` but with **dummy or separate keys**.

### Optional: reference KV_URL directly

If you prefer not to duplicate the KV URL, you can modify `main.py` to read `REDIS_URL` or fall back to `KV_URL`:

```python
REDIS_URL = os.getenv("REDIS_URL") or os.getenv("KV_URL")
limiter = build_limiter(REDIS_URL)
```

This step is optional. The rest of this guide assumes you set `REDIS_URL` explicitly.

---

## Step 7 — Deploy

1. Push your latest code to the main branch.
2. Vercel automatically triggers a production deployment.
3. Wait for the build to finish.

The app should now be live at `https://your-project.vercel.app`.

---

## Step 8 — Post-deploy verification

Run these checks immediately after deploy.

### 8.1 Health check

```bash
curl https://your-project.vercel.app/health
```

Expected response:
```json
{"status": "healthy", "database": "ok"}
```

It must **not** contain `database_url`.

### 8.2 Sign up and log in

Use the deployed UI to:
1. Create an account.
2. Log in.
3. Start a chat.

### 8.3 Verify rate limiting

Run this from your terminal to confirm rate limiting works:

```bash
for i in {1..35}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST https://your-project.vercel.app/api/chat \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -d '{"message":"bonjour"}'
done
```

You should see mostly `200` responses, then `429 Too Many Requests` after the limit.

### 8.4 Verify Redis is being used

If you have Redis CLI installed:

```bash
redis-cli -u REDIS_URL keys '*'
```

You should see keys related to slowapi rate limits.

### 8.5 Check Vercel function logs

In the Vercel dashboard:
1. Go to **Deployments**.
2. Click the latest deployment.
3. Click **Functions** → select the function → view logs.

Look for any `NVIDIA API error` or database connection errors.

---

## Security checklist

Before announcing the app publicly, confirm:

- [ ] `.env` is not committed to git.
- [ ] Old `NVIDIA_API_KEY` revoked in NVIDIA dashboard.
- [ ] New `NVIDIA_API_KEY` only in Vercel env vars.
- [ ] `JWT_SECRET` is 64 random hex characters.
- [ ] `COOKIE_SECURE=true` and `COOKIE_SAMESITE=lax` in Vercel.
- [ ] `DATABASE_URL` points to Supabase Postgres, not SQLite.
- [ ] `REDIS_URL` points to Vercel KV.
- [ ] `/health` does not leak `database_url`.
- [ ] HTTPS is enforced by Vercel.
- [ ] All sensitive endpoints return `401` when not authenticated.
- [ ] Rate limiting returns `429` after thresholds.
- [ ] Shared conversation links behavior is intentional (public by design).

---

## Monitoring & maintenance

### Routine checks

| Task | Frequency | How |
|---|---|---|
| Check Vercel function error logs | Weekly | Dashboard → Deployments → Functions |
| Monitor NVIDIA API usage & billing | Weekly | https://build.nvidia.com/ |
| Check Supabase database size | Monthly | Supabase dashboard |
| Rotate `JWT_SECRET` | Every 6–12 months | Generate new secret, redeploy, force logout users |
| Rotate `NVIDIA_API_KEY` | If ever suspected leaked | Revoke old, generate new, update Vercel |

### Backups

Supabase automatically backs up Postgres. Verify the backup retention policy in Supabase settings.

For extra safety, schedule a nightly logical backup:

```bash
pg_dump DATABASE_URL > parlez-backup-$(date +%F).sql
```

### Updating the app

1. Test changes locally with Supabase connection:
   ```bash
   JWT_SECRET=$(openssl rand -hex 32) NVIDIA_API_KEY=dummy DATABASE_URL=postgresql://... REDIS_URL=redis://... venv/bin/python main.py
   ```
2. Run tests:
   ```bash
   JWT_SECRET=$(openssl rand -hex 32) NVIDIA_API_KEY=dummy venv/bin/python -m pytest tests/ -q
   ```
3. Commit and push. Vercel deploys automatically.

---

## Troubleshooting

### `500 Internal Server Error` on every request

Check Vercel function logs. Common causes:
- Missing env var (`NVIDIA_API_KEY`, `JWT_SECRET`, `DATABASE_URL`).
- `DATABASE_URL` uses `postgres://` instead of `postgresql://`. SQLAlchemy requires `postgresql://`.
- Supabase IP restrictions block Vercel. In Supabase, go to **Project Settings → Database → Network Bans / IPv4** and allow Vercel IPs, or use Supabase's connection pooling.

### `NVIDIA API error: 401`

- The `NVIDIA_API_KEY` is missing or invalid.
- Rotate the key in the NVIDIA dashboard and update Vercel env vars.

### Rate limiting not working across instances

- `REDIS_URL` is not set.
- `REDIS_URL` points to a Redis instance that is unreachable from Vercel.
- Verify with `redis-cli -u REDIS_URL ping`.

### `429 Too Many Requests` for legitimate users

- The default limits may be too aggressive for your traffic.
- Adjust the `@limiter.limit("...")` decorators in `main.py`.

### Chat responses are slow

- NVIDIA NIM cold-start latency is normal.
- Consider enabling streaming responses (requires code changes).
- Check Vercel function timeout; the Hobby plan has a 10-second limit.

### Cookies not working / users logged out

- Ensure `COOKIE_SECURE=true` and the app is served over HTTPS.
- For local HTTP testing, temporarily set `COOKIE_SECURE=false`.

---

## Rollback procedure

If a deployment breaks:

1. In the Vercel dashboard, go to **Deployments**.
2. Find the last working deployment.
3. Click the three dots → **Promote to Production**.
4. If the issue is a leaked secret, rotate the secret before promoting.

---

## Appendix: Migrate SQLite to Supabase

If you have existing SQLite data in `data/parlez.db`:

1. Export SQLite to SQL:
   ```bash
   sqlite3 data/parlez.db .dump > parlez.sql
   ```
2. Edit `parlez.sql`:
   - Remove SQLite-specific PRAGMAs.
   - Convert `AUTOINCREMENT` to PostgreSQL `SERIAL` or identity columns if needed.
3. Import into Supabase:
   ```bash
   psql DATABASE_URL < parlez.sql
   ```
4. Verify tables exist:
   ```bash
   psql DATABASE_URL -c "\dt"
   ```

For the Parlez schema, `users`, `shared_links`, and `comments` tables are usually enough because user data is stored as JSON columns.

---

## Quick reference: env vars

```bash
NVIDIA_API_KEY=nvapi-...
JWT_SECRET=$(openssl rand -hex 32)
DATABASE_URL=postgresql://postgres:...@db....supabase.co:5432/postgres
REDIS_URL=redis://default:...@....kv.vercel-storage.com:6379
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
TOKEN_EXPIRY_HOURS=24
```

Keep this guide and your Vercel/Supabase credentials in a secure password manager for future reference.
