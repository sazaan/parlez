# Learning Chatbot - Powered by NVIDIA NIM

A self-study chatbot that helps you learn from images, videos, PDFs, and other media using NVIDIA's Nemotron 3 Nano Omni model.

## Features

- **Image Analysis** - JPG, PNG, GIF, WebP (understands visual content)
- **Video Analysis** - MP4, AVI, MOV, MKV, WebM (analyzes video content)
- **PDF Processing** - Extract and discuss document content
- **Text/Code Analysis** - Explain code, notes, articles
- **Omni-modal Reasoning** - Nemotron 3 understands images, video, speech, and text

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
Frontend (HTML/JS)  →  Backend (FastAPI)  →  NVIDIA NIM API
                            ↓                 (Nemotron 3 Nano Omni)
                    Document Processing
                    - PDF extraction (PyPDF2)
                    - Image/Video base64 encoding
                    - Text parsing
```

## Model: Nemotron 3 Nano Omni

- **Model ID**: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`
- **Capabilities**: Images, Video, Speech, Text
- **Reasoning**: Built-in thinking/reasoning mode
- **Provider**: NVIDIA NIM

## How It Works

1. **Upload a file** (image, video, PDF, or text)
2. **Nemotron 3 Nano Omni analyzes** the content using omni-modal reasoning
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
| Model | Nemotron 3 Nano Omni | GPT-4 Vision |
| Video | ✅ Native support | ❌ Not supported |
| Reasoning | Built-in thinking mode | Standard |
| Cost | Free tier available | Pay per token |
| Omni-modal | ✅ Images, Video, Speech, Text | Limited |

## Cost Considerations

- **NVIDIA NIM**: Free tier available, then pay-per-use
- **Typical session**: $0.05-0.20 (varies by usage)
- **Images**: ~$0.01-0.03 per analysis
- **Videos**: ~$0.05-0.15 per analysis
- **Text**: ~$0.01-0.05 per 1K tokens

Tip: Use the free tier for experimentation!

## Features Enabled

- **Thinking Mode**: Model shows reasoning process
- **Reasoning Budget**: Configurable thinking depth
- **Omni-modal**: Single model handles all media types
- **High Resolution**: Detailed image/video analysis

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

### Run tests

```bash
python -m pytest tests/
```

## License
mimo -s REMOVED
MIT License
