#!/usr/bin/env bash
# Build script for SkyScraper.bot deployment on Render

set -o errexit  # Exit on any command failure

echo "🚀 Starting SkyScraper.bot build process..."

# Update system packages
echo "📦 Updating system packages..."
apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    pkg-config

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install additional dependencies for web scraping
echo "🕸️ Installing web scraping dependencies..."
pip install playwright
playwright install chromium

# Set up environment variables
echo "⚙️ Setting up environment..."
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data
mkdir -p temp

# Run any database migrations (if needed)
echo "🗄️ Setting up database..."
# python -m alembic upgrade head  # Uncomment if using Alembic for migrations

# Download language models (if using spaCy or similar)
echo "🧠 Setting up AI models..."
# python -m spacy download en_core_web_sm  # Uncomment if using spaCy

# Set up logging
echo "📝 Configuring logging..."
touch logs/app.log
chmod 666 logs/app.log

# Optimize Python bytecode
echo "⚡ Optimizing Python..."
python -m compileall -b .
find . -name "*.py" -delete  # Remove source files, keep only bytecode (optional)

# Clear cache
echo "🧹 Cleaning up..."
pip cache purge
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "✅ Build completed successfully!"
echo "🌐 SkyScraper.bot is ready for deployment"

# Health check
echo "🔍 Running health check..."
python -c "
import sys
import importlib
required_modules = ['fastapi', 'uvicorn', 'httpx', 'pydantic']
for module in required_modules:
    try:
        importlib.import_module(module)
        print(f'✅ {module} imported successfully')
    except ImportError as e:
        print(f'❌ Failed to import {module}: {e}')
        sys.exit(1)
print('🎉 All required modules are available!')
"

echo "🚀 Ready to start SkyScraper.bot API server!"
