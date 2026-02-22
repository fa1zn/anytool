#!/usr/bin/env bash
# Run Anytool API locally (Mac/Linux). Activate venv first: source .venv/bin/activate
set -e
cd "$(dirname "$0")"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
