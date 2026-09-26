#!/usr/bin/env bash
# ============================================================
# run.sh — Application startup script
# ============================================================
set -euo pipefail

# Load environment variables from .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Ensure data directories exist
mkdir -p data/review_history data/config_rules

# Install dependencies if venv doesn't exist yet
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --no-cache-dir -q -r requirements.txt

echo "Starting AI Code Reviewer on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --reload