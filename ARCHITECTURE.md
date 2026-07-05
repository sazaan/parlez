# How It Works - NVIDIA NIM Integration

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   Learning Chatbot (NVIDIA NIM)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Frontend   │      │    Backend   │      │  NVIDIA NIM  │  │
│  │   (HTML/JS)  │ ───► │   (FastAPI)  │ ───► │   (Nemotron) │  │
│  │              │ ◄─── │              │ ◄─── │              │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                     │                     │            │
│         │                     │                     │            │
│    Upload files         Process files          Omni-modal       │
│    Display chat         Encode media           Analysis         │
│                         Handle PDFs            Reasoning         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Nemotron 3 Nano Omni

**Model ID**: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`

### Capabilities

- 🖼️ **Image Understanding** - Analyze visual content, diagrams, equations
- 🎬 **Video Analysis** - Process video files, describe scenes
- 🎤 **Speech Recognition** - Understand audio content
- 📝 **Text Analysis** - Read and explain documents, code
- 💡 **Reasoning** - Built-in thinking mode for complex problems

### Why Nemotron?

| Feature | Nemotron 3 Nano Omni | GPT-4 Vision |
|---------|---------------------|--------------|
| Video Support | ✅ Native | ❌ Not supported |
| Reasoning Mode | ✅ Built-in thinking | ❌ Standard |
| Omni-modal | ✅ Single model | ⚠️ Separate models |
| Cost | Free tier available | Pay per token |
| Provider | NVIDIA NIM | OpenAI |

## How Each Feature Works

### 1. Image Analysis (Omni-modal)

```
User uploads image → FastAPI receives → Base64 encode → 
Send to Nemotron → Omni-modal analysis → Educational response
```

**Example:**
- Upload a math equation screenshot
- AI: "This shows the Pythagorean theorem: a² + b² = c²..."
- Ask: "Can you prove this?"
- AI provides step-by-step proof

### 2. Video Analysis (Omni-modal)

```
User uploads video → FastAPI receives → Base64 encode → 
Send to Nemotron → Video understanding → Detailed breakdown
```

**Example:**
- Upload a lecture clip
- AI: "This video explains photosynthesis..."
- Ask: "What are the key steps shown?"
- AI describes the process

### 3. PDF Processing

```
User uploads PDF → Extract text with PyPDF2 → 
Send to Nemotron → Text analysis → Summary/answers
```

**Example:**
- Upload textbook page
- AI: "This chapter covers machine learning basics..."
- Ask: "Explain supervised vs unsupervised learning"
- AI provides clear comparison

### 4. Text/Code Analysis

```
User uploads file → Read content → 
Send to Nemotron → Code explanation → Learning response
```

**Example:**
- Upload Python function
- AI: "This function implements binary search..."
- Ask: "What's the time complexity?"
- AI explains O(log n)

## NVIDIA NIM API Integration

### Method 1: OpenAI Client (Recommended)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

response = client.chat.completions.create(
    model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Method 2: Direct API Call

```python
import requests

headers = {
    "Authorization": f"Bearer {NVIDIA_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "messages": [{"role": "user", "content": ""}],
    "max_tokens": 8192,
    "temperature": 0.6,
    "top_p": 0.95
}

response = requests.post(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    headers=headers,
    json=payload
)
```

### Multimodal Content

```python
# Image
content = [
    {"type": "text", "text": "Describe this image"},
    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
]

# Video
content = [
    {"type": "text", "text": "What's in this video?"},
    {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{b64}"}}
]
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/upload` | POST | Upload & analyze media |
| `/chat` | POST | Send chat message |
| `/history` | GET | Get conversation history |
| `/history` | DELETE | Clear history |
| `/models` | GET | Model information |

## Cost Breakdown

| Operation | Provider | Cost |
|-----------|----------|------|
| Image analysis | NVIDIA NIM | Free tier / $0.01-0.03 |
| Video analysis | NVIDIA NIM | Free tier / $0.05-0.15 |
| PDF/Text analysis | NVIDIA NIM | Free tier / $0.01-0.05 |
| Chat follow-up | NVIDIA NIM | Free tier / $0.01-0.03 |

**Typical session cost:** $0.00-0.20 (free tier available!)

### Getting Your API Key

1. Go to https://build.nvidia.com/
2. Sign up / Log in
3. Navigate to API Keys
4. Generate new key
5. Add to `.env` file

## Security Notes

- API key stored in `.env` (never committed to git)
- Files processed in memory (not stored)
- No persistent storage (reset on restart)
- Add auth for production use

## Extending the Application

### Add Audio Support

```python
def is_audio_file(extension: str) -> bool:
    return extension in ["mp3", "wav", "ogg", "m4a"]

# In upload endpoint
elif is_audio_file(extension):
    b64_data = encode_file_to_base64(file_bytes, get_mime_type(extension))
    content = [
        {"type": "text", "text": "Transcribe and explain this audio"},
        {"type": "audio_url", "audio_url": {"url": f"data:{get_mime_type(extension)};base64,{b64_data}"}}
    ]
```

### Add Streaming Responses

```python
# Enable streaming
payload["stream"] = True

# Process stream
for line in response.iter_lines():
    if line:
        data = json.loads(line)
        # Yield chunks to frontend
```

### Add User Authentication

```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/upload")
async def upload_file(file: UploadFile, token = Depends(security)):
    # Verify token
    pass
```

## Troubleshooting

### Common Issues

1. **"NVIDIA API error: 401"**
   - Check API key is valid
   - Ensure `.env` has correct key

2. **"File too large"**
   - Max: 20MB per upload
   - Compress or extract portions

3. **"Rate limit exceeded"**
   - Wait and retry
   - Upgrade plan if needed

4. **"Video processing failed"**
   - Check video format support
   - Try smaller files

### Supported Formats

**Images**: JPG, JPEG, PNG, GIF, WebP  
**Videos**: MP4, AVI, MOV, MKV, WebM  
**Documents**: PDF  
**Text**: TXT, MD, PY, JS, TS, JSON, CSV, XML, HTML, CSS

## Performance Tips

1. **Use reasonable file sizes** - Under 10MB recommended
2. **Ask specific questions** - Reduces token usage
3. **Clear history** - Start fresh for new topics
4. **Batch uploads** - Process related files together

## Future Enhancements

- [ ] Real-time streaming responses
- [ ] OCR for scanned PDFs
- [ ] User accounts & history
- [ ] Audio transcription
- [ ] Study flashcards
- [ ] Learning progress tracking
- [ ] Collaborative features
- [ ] Mobile app
