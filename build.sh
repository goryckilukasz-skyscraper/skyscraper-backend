#!/usr/bin/env bash
set -o errexit

echo "🚀 Building SkyScraper.bot Backend..."
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

echo "🎭 Installing Playwright and Chromium..."
playwright install --with-deps chromium

echo "✅ Build completed successfully!"
