# Deploying Parlez to Vercel with Supabase + NVIDIA NIM

## Quick Start (5 minutes)

### 1. Create Supabase Project
- Go to [supabase.com](https://supabase.com) → New Project
- Save your database password
- Go to Settings → Database → Connection string → URI
- Copy: `postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres`

### 2. Get NVIDIA API Key
- Go to [build.nvidia.com](https://build.nvidia.com)
- Search for `z-ai/glm-5.1`
- Click "Get API Key" → copy the key (starts with `nvapi-`)

### 3. Prepare the Database
```bash
# Set your Supabase URL
export DATABASE_URL="postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres"

# Run the prep script (switches to PostgreSQL, creates tables)
./scripts/prepare-vercel.sh
```

### 4. Deploy to Vercel
```bash
# Push to GitHub
git add -A
git commit -m "Prepare for Vercel deployment"
git push

# Import on Vercel.com → Add New → Project → Import your repo
```

### 5. Set Environment Variables in Vercel

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Your Supabase connection string |
| `NEXTAUTH_SECRET` | Run `openssl rand -base64 32` locally, paste the result |
| `NEXTAUTH_URL` | `https://your-app.vercel.app` (your Vercel URL) |
| `AUTH_TRUST_HOST` | `true` |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` |
| `NVIDIA_API_KEY` | `nvapi-your-key-here` |

### 6. Deploy!
Click Deploy on Vercel. The `postinstall` script runs `prisma generate` automatically.

---

## Architecture

```
User's Browser
    ↓
Vercel (Next.js)
    ├── /api/chat          → NVIDIA NIM (z-ai/glm-5.1) for AI tutor
    ├── /api/translate     → NVIDIA NIM for translation
    ├── /api/generate-test → NVIDIA NIM for AI question generation
    ├── /api/tts           → Google Translate TTS (free, natural French voice)
    ├── /api/prebuilt-questions → Pre-built JSON (bundled at build time)
    ├── /api/auth/*        → NextAuth.js (JWT sessions)
    └── /api/progress      → Supabase PostgreSQL (user progress)
```

## No ZAI SDK Dependency

The app no longer uses `z-ai-web-dev-sdk`. All AI calls go through a custom `chatCompletion()` function in `src/lib/ai-client.ts` that:
- Uses standard `fetch()` to call the OpenAI-compatible NVIDIA NIM endpoint
- Sends standard headers (`Authorization: Bearer nvapi-...`)
- Works with any OpenAI-compatible API endpoint

## Database Schema

The Prisma schema uses SQLite for local dev. For Vercel:
1. The `prepare-vercel.sh` script changes `provider = "postgresql"`
2. `postinstall` in `package.json` runs `prisma generate`
3. Tables are created by `prisma db push` (run locally before deploying)

## Local Development

```bash
# .env
DATABASE_URL="file:./dev.db"
# AI features work in sandbox (falls back to /etc/.z-ai-config)
# Or set NVIDIA_API_KEY for local testing with NVIDIA NIM
```

## Troubleshooting

### "Prisma Client not found"
The `postinstall` script runs `prisma generate`. If it fails, add this to Vercel build settings:
- Build Command: `npx prisma generate && next build`

### "Database connection failed"
- Verify `DATABASE_URL` is correct
- Supabase free tier pauses after 7 days of inactivity — unpause in dashboard

### "AI API error 401"
- Check `NVIDIA_API_KEY` is set correctly (starts with `nvapi-`)
- Verify `NVIDIA_BASE_URL` is `https://integrate.api.nvidia.com/v1`

### "Pre-built questions not found"
- The `prebuilt-bank.json` file (944KB) is committed to the repo
- It's imported at build time — no filesystem access needed on Vercel

### "TTS not working"
- The TTS API fetches from Google Translate server-side
- Works on Vercel serverless functions (no API key needed)
- If rate-limited, falls back to browser SpeechSynthesis
