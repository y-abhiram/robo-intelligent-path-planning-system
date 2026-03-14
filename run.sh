#!/bin/bash

# Wall Finishing Robot Control System - Startup Script

echo "🤖 Wall Finishing Robot Control System"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Start the server
echo "🚀 Starting server at http://localhost:8000"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🖥️  Web Interface: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
