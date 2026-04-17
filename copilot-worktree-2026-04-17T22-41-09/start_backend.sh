#!/bin/bash
# Quick start script for the Real Estate Agent backend

echo "🚀 Real Estate Agent Backend - Quick Start"
echo "=========================================="
echo ""

# Step 1: Check if .env exists
if [ ! -f .env ]; then
    echo "📋 Step 1: Setting up environment variables..."
    cp .env.example .env
    echo "✓ Created .env from .env.example"
    echo "⚠️  Please edit .env and add your GEMINI_API_KEY"
    echo ""
    read -p "Press Enter when ready to continue..."
fi

# Step 2: Check Docker
echo ""
echo "🐳 Step 2: Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi
echo "✓ Docker is installed"

# Step 3: Start services
echo ""
echo "🔨 Step 3: Building and starting services..."
echo "(This may take 1-2 minutes on first run)"
echo ""
docker compose up --build

# Show next steps
echo ""
echo "✅ Backend is running!"
echo ""
echo "📚 API Documentation:"
echo "   🌐 Open http://localhost:8000/docs in your browser"
echo ""
echo "🧪 Quick Tests:"
echo "   Health check:  curl http://localhost:8000/health"
echo "   All predictions: curl http://localhost:8000/api/predictions"
echo "   Stats: curl http://localhost:8000/api/stats"
echo ""
echo "📖 For more info, read BACKEND_SETUP.md"
