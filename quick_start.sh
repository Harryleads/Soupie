#!/bin/bash

echo "🧠 Soupie - Quick Start Setup"
echo "=============================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip first."
    exit 1
fi

echo "✅ Python and pip are installed"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp env.example .env
    echo "📝 Please edit .env file with your database and API keys"
    echo "   - DATABASE_URL: Your NeonDB connection string"
    echo "   - JWT_SECRET: Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    echo "   - SECRET_KEY: Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    echo "   - GEMINI_API_KEY: Your Google Gemini API key (optional for testing)"
fi

echo ""
echo "🚀 Setup complete! To start the server:"
echo "   source venv/bin/activate"
echo "   python run_local.py"
echo ""
echo "📖 For detailed setup instructions, see setup_local.md"
