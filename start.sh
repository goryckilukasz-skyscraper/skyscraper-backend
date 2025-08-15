#!/usr/bin/env bash
echo "🚀 Starting SkyScraper.bot API Server..."
echo "🌍 Environment: ${ENVIRONMENT:-development}"
echo "🔧 Port: ${PORT:-8000}"

uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
