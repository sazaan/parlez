#!/bin/bash

# Learning Chatbot - Simple Docker Run (without compose)

echo "📚 Learning Chatbot - NVIDIA NIM (Docker)"
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

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo ""
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "Please edit .env and add your NVIDIA API key:"
    echo "  nano .env"
    echo ""
    echo "Get your API key at: https://build.nvidia.com/"
    exit 1
fi

# Check if API key is set
if grep -q "your-nvidia-api-key-here" .env; then
    echo "⚠️  Please update .env with your actual NVIDIA API key!"
    echo ""
    echo "Edit .env and add your key:"
    echo "  nano .env"
    echo ""
    echo "Get yours at: https://build.nvidia.com/"
    exit 1
fi

# Source .env to get API key
export $(grep -v '^#' .env | xargs)

echo "🐳 Building Docker image..."
docker build -t learning-chatbot .

echo ""
echo "🚀 Starting Learning Chatbot..."
echo "📖 Open http://localhost:8000 in your browser"
echo "🤖 Model: NVIDIA Nemotron 3 Nano Omni"
echo "Press Ctrl+C to stop"
echo ""

docker run -d \
    --name learning-chatbot \
    -p 8000:8000 \
    -e NVIDIA_API_KEY="$NVIDIA_API_KEY" \
    --restart unless-stopped \
    learning-chatbot

echo ""
echo "✅ Container started!"
echo ""
echo "View logs: docker logs -f learning-chatbot"
echo "Stop:      docker stop learning-chatbot"
echo "Remove:    docker rm learning-chatbot"
