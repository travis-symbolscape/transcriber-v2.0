#!/bin/bash

# Transcriber v2.0 Installation Script
# This script sets up the environment and installs dependencies

set -e

echo "🎯 Transcriber v2.0 Installation"
echo "================================"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "📍 Python version: $python_version"

# Check if Python is 3.8+
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "✅ Python version is compatible"
else
    echo "❌ Python 3.8+ required. Please upgrade Python."
    exit 1
fi

# Check for FFmpeg
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg found"
else
    echo "⚠️  FFmpeg not found"
    echo "📝 Audio preprocessing requires FFmpeg"
    echo "   macOS: brew install ffmpeg"
    echo "   Ubuntu: sudo apt-get install ffmpeg"
    echo "   Windows: Download from https://ffmpeg.org/download.html"
    echo ""
    read -p "Continue without FFmpeg? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env file..."
    cp .env.template .env
    echo "📝 Please edit .env and add your OpenAI API key"
fi

# Create input and output directories
mkdir -p input output

# Make scripts executable
chmod +x run_transcription_pipeline_v2.py
find scripts -name "*.py" -exec chmod +x {} \;

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your API keys:"
echo "   - OpenAI API key (for AI context correction \u0026 translation)"
echo "   - Hugging Face token (for advanced speaker diarization)"
echo "2. Place video/audio files in the 'input' directory"
echo "3. Run: python run_transcription_pipeline_v2.py"
echo ""
echo "📖 For detailed instructions, see README.md"
