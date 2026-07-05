#!/bin/bash

# Learning Chatbot - Docker Quick Start

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

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    echo ""
    echo "Install Docker Compose:"
    echo "  sudo apt install docker-compose"
    echo "  Or visit: https://docs.docker.com/compose/install/"
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

echo "🐳 Building Docker container..."
docker compose build

echo ""
echo "🚀 Starting Learning Chatbot..."
echo "📖 Open http://localhost:8000 in your browser"
echo "🤖 Model: NVIDIA Nemotron 3 Nano Omni"
echo "Press Ctrl+C to stop"
echo ""

docker compose up
