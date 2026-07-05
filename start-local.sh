#!/bin/bash

# Learning Chatbot - Local Setup (without Docker)

echo "📚 Learning Chatbot - NVIDIA NIM (Local)"
echo "========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python version: $PYTHON_VERSION"

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

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        echo ""
        echo "Try installing python3-venv:"
        echo "  sudo apt install python3.12-venv"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "🚀 Starting Learning Chatbot..."
echo "📖 Open http://localhost:8000 in your browser"
echo "🤖 Model: NVIDIA Nemotron 3 Nano Omni"
echo "Press Ctrl+C to stop"
echo ""

# Run the server
python main.py
