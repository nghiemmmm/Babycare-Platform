#!/usr/bin/env bash
set -e

echo "========================================================"
echo " [BabyCare AI] Starting Pre-flight System Health Checks"
echo "========================================================"

# 1. Run database & infrastructure connectivity health-checks
python -m app.backend_pre_start

echo "========================================================"
echo " [BabyCare AI] Pre-flight Checks Passed! Launching App"
echo "========================================================"

# 2. Launch FastAPI application
exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
