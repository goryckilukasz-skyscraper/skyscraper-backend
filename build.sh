#!/usr/bin/env bash
set -o errexit

echo "🚀 Building SkyScraper.bot Backend..."
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

echo "🎭 Installing Playwright (lightweight)..."
# Install playwright first
playwright install-deps
# Then install only chromium (smaller footprint)
playwright install chromium

echo "✅ Build completed successfully!"
