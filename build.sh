#!/usr/bin/env bash
# Build script for SkyScraper.bot deployment on Render

set -o errexit  # Exit on any command failure

echo "🚀 Starting SkyScraper.bot build process..."

# Update pip to latest version
echo "🐍 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🕸️ Installing Playwright browsers..."
pip install playwright
playwright install chromium

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data
mkdir -p temp

# Set up logging
echo "📝 Setting up logging..."
touch logs/app.log || true

# Health check - verify critical modules can be imported
echo "🔍 Running health check..."
python -c "
import sys
try:
    import fastapi
    import uvicorn
    import httpx
    import pydantic
    print('✅ All critical modules imported successfully!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

echo "✅ Build completed successfully!"
echo "🌐 SkyScraper.bot backend is ready for deployment!"
