> **Project documentation:** See [Parlez — Project Overview](docs/PROJECT_OVERVIEW.md)
> for the current product scope, Canadian immigration research, architecture,
> AI-provider comparison, pricing analysis, and roadmap. A formatted, printable
> version is available in [docs/PROJECT_OVERVIEW.html](docs/PROJECT_OVERVIEW.html).
> The older setup guide below contains historical product descriptions; the
> overview distinguishes implemented features from proposed functionality.

# Learning Chatbot - Powered by NVIDIA NIM

Parlez is a self-study French-learning app for text-based tutoring and writing feedback. It defaults to NVIDIA NIM model `nvidia/nemotron-3.5-lightning-30b-a3b`; a same-origin admin console can switch the active provider and model among configured NVIDIA, Gemini, OpenRouter, and OpenCode Zen chat-completions endpoints.

## Features

- **Image Analysis** - JPG, PNG, GIF, WebP (understands visual content)
- **Video Analysis** - MP4, AVI, MOV, MKV, WebM (analyzes video content)
- **PDF Processing** - Extract and discuss document content
- **Text/Code Analysis** - Explain code, notes, articles
- **Text-based AI tutor** - Current chat and writing-correction requests send text to NVIDIA NIM; media input requires additional application support

## Quick Start

### Option 1: Docker (Recommended for local use)

```bash
# 1. Get API key from https://build.nvidia.com/
# 2. Edit .env with your key
nano .env

# 3. Run with Docker Compose
./run.sh
```

### Option 2: Local Installation

```bash
# 1. Get API key from https://build.nvidia.com/
# 2. Edit .env with your key
nano .env

# 3. Run local setup
./start-local.sh
```

### Option 3: Manual Docker

```bash
# Build and run with single command
./docker-run.sh
```

### Deploy to Vercel + Supabase + Redis (production)

See [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) for a complete, step-by-step guide.

## Setup

### 1. Get NVIDIA API Key

1. Go to https://build.nvidia.com/
2. Sign up or log in
3. Navigate to API Keys
4. Generate a new API key

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
# Add your NVIDIA_API_KEY
```

### 3. Run the Application

```bash
# Docker (recommended)
./run.sh

# Or local
./start-local.sh
```

Server starts at `http://localhost:8000`

## Architecture

```
Frontend (HTML/JS)  →  Backend (FastAPI)  →  Active AI provider
                            ↓                 (default: NVIDIA Nemotron 3.5 Lightning)
                    Document Processing
                    - PDF extraction (PyPDF2)
                    - Image/Video base64 encoding
                    - Text parsing
```

## Current AI model

- **Default model ID**: `nvidia/nemotron-3.5-lightning-30b-a3b` ([NVIDIA Build](https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b))
- **Model I/O**: text in, text out; the current Parlez chat and writing-correction code sends text-only payloads
- **Bootstrap configuration**: `NVIDIA_MODEL` selects the NVIDIA default; the admin console can switch the active provider/model at runtime
- **Availability**: NVIDIA Build currently lists a free endpoint for this model; free-tier access and limits can change
- **Previous default**: `nvidia/nemotron-3-nano-30b-a3b` still has a partner endpoint, but its free endpoint is marked deprecated ([NVIDIA Build](https://build.nvidia.com/nvidia/nemotron-3-nano-30b-a3b))

Choosing a multimodal model ID does not itself add image, audio, or video support—the application must send those modalities in the request payload.

## Admin panel and provider management

The admin console is served by the same Parlez backend at `/parlez-admin` (override with `ADMIN_PATH` in `.env`). The path is not a security control; admin APIs require a dedicated username, bcrypt password hash, TOTP authenticator code, and a short-lived signed admin session.

Run `./run.sh` from an interactive terminal to start Docker Compose. If `.env` does not exist, the script creates it from `.env.example`. On the first run—or whenever one of the four admin credentials is missing—it builds the app image and runs `scripts/generate_admin_credentials.py` inside that image. Choose an admin username and password when prompted; the generated hash, TOTP secret, and session-signing key are written directly into the ignored `.env` file, which is restricted to owner-only permissions. The authenticator enrollment URI is displayed once; add it to your authenticator app and keep it private. Existing complete admin credentials are retained on later runs.

Add at least one provider key to `.env`: `NVIDIA_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, and/or `OPENCODE_ZEN_API_KEY`. The portal only permits selecting providers with a server-side key present; keys are never sent back to the browser. `OPENCODE_API_KEY` is also accepted as an alias. If no supported provider key is set, `run.sh` saves the admin credentials and then asks you to add a key before running it again. For manual setup outside Docker, install the app dependencies and run `python scripts/generate_admin_credentials.py --env-file .env`.

Set `COOKIE_SECURE=true` in production and serve the app over HTTPS. Then visit `https://your-host/parlez-admin`. The portal tests a provider/model using a synthetic prompt before activation, keeps the ten most recent previous configurations, and can restore them without editing `.env`.

The selected provider/model and course publication flags are stored in the configured database. The `.env` file supplies secrets and bootstrap defaults; the web panel does not rewrite it. Provider endpoints are fixed in backend code rather than admin-editable URLs. Use database backups when operating the panel.

The course panel can publish A2, B1, and B2 levels and individual modules. These levels remain off by default. Their current source data is sparse compared with A1, so review lesson coverage and public-facing course copy before enabling them. Publication controls are enforced at both the learner UI and course API.


## How It Works

1. **Upload a file** (image, video, PDF, or text)
2. **The configured AI provider/model processes** the text prompt through its chat-completions endpoint
3. **Ask questions** about the content - "Explain this", "Summarize", "What does X mean?"
4. **Get learning responses** - The chatbot provides educational explanations

## API Endpoints

- `POST /upload` - Upload a file and get analysis
- `POST /chat` - Send message with context
- `GET /history` - Get conversation history
- `DELETE /history` - Clear conversation history
- `GET /models` - Get model information

## Supported File Types

- **Images**: JPG, JPEG, PNG, GIF, WebP (omni-modal analysis)
- **Videos**: MP4, AVI, MOV, MKV, WebM (omni-modal analysis)
- **Documents**: PDF (text extraction + analysis)
- **Text**: TXT, MD, code files (direct analysis)

## Example Usage

1. Upload a math equation image → Ask "Solve this step by step"
2. Upload a lecture video → Ask "Summarize the key points"
3. Upload a textbook PDF → Ask "Explain this concept"
4. Upload code → Ask "What does this function do?"
5. Upload a scientific diagram → Ask "Describe the process shown"

## NVIDIA NIM vs OpenAI

| Feature | NVIDIA NIM | OpenAI |
|---------|-----------|--------|
| Model | Nemotron 3.5 Lightning (default) | GPT-4 Vision |
| Video in current Parlez flow | Not sent by this app | API-dependent |
| Reasoning | Depends on selected model; no special reasoning budget is sent | Provider-dependent |
| Cost | Free tier available | Pay per token |
| Input modalities in current app | Text only | Text and image capabilities vary by API |

## Cost Considerations

- **NVIDIA NIM**: Free tier available, then pay-per-use
- **Typical session**: $0.05-0.20 (varies by usage)
- **Images**: ~$0.01-0.03 per analysis
- **Videos**: ~$0.05-0.15 per analysis
- **Text**: ~$0.01-0.05 per 1K tokens

Tip: Use the free tier for experimentation!

## Current model integration

- **Text chat completions**: The current app sends text-only messages to the active configured provider.
- **Model selection**: `NVIDIA_MODEL` is the NVIDIA fallback/default; the admin console can set the active provider/model at runtime.
- **Model-specific capabilities**: Reasoning and supported modalities depend on the selected endpoint; they are not enabled solely by changing the model ID.

## Limitations

- File size limit: 20MB per upload (NVIDIA NIM limit)
- PDF text extraction may not work for scanned documents
- No persistent storage - conversations reset on server restart
- Video processing may take longer for large files

## Docker Commands

```bash
# Start
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down

# Rebuild
docker compose build --no-cache
```

## Troubleshooting

### Common Issues

For Listen-button playback and microphone problems, see
[Voice troubleshooting](docs/VOICE_TROUBLESHOOTING.md).

1. **"NVIDIA API error: 401"**
   - Check your API key is valid
   - Ensure `.env` file has correct key

2. **"File too large"**
   - Maximum file size: 20MB
   - Compress files or extract portions

3. **"Could not extract text from PDF"**
   - PDF might be scanned (image-based)
   - Consider using image upload instead

4. **"Rate limit exceeded"**
   - Wait a few seconds and retry
   - Upgrade to paid tier for higher limits

5. **Docker issues**
   - Ensure Docker is running: `sudo systemctl start docker`
   - Check container status: `docker ps`

## Development

### Run in development mode

```bash
# Local development
./start-local.sh

# Or with Docker
docker compose up
```

### Docker data permissions

The container runs as a non-root `appuser`. Both Compose configurations run a
one-shot `data-init` service as root to give that user ownership of the bind-mounted
`./data` directory before the app starts. This fixes `sqlite3.OperationalError:
unable to open database file` caused by data created by older root-running
containers (or by Docker creating the host directory as root).

Use a current Docker Compose v2 release, then rebuild and start:

```bash
docker compose down
docker compose up --build -d
docker compose logs --tail=50 data-init chatbot
```

`data-init` exiting with code **0** is expected. Existing database contents are
preserved; do not delete `data/` or `parlez.db` to resolve this error. Ownership of
`./data` on the host changes to the container user's numeric UID/GID, so host-side
file management may require `sudo`. Only the initializer runs as root; the app
continues to run as `appuser`.

The default database is `/app/data/parlez.db` inside Docker. If you set
`DATABASE_URL` in `.env`, ensure it uses a valid **container** path with a writable
parent directory; this initializer only manages `/app/data`. For the default
SQLite database, omit `DATABASE_URL` or use
`DATABASE_URL=sqlite:////app/data/parlez.db`.

The obsolete Compose `version` warning is removed. A missing Buildx/Bake warning
is separate from the SQLite crash; install Docker's Buildx plugin if needed.

### Run tests

```bash
python -m pytest tests/
```

## License

MIT License. See [`LICENSE`](./LICENSE) (or add a `LICENSE` file with your chosen terms before public release).
