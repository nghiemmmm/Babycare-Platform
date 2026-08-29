#!/usr/bin/env bash
# ==============================================================================
# BabyCare AI - Shell Environment Switcher Wrapper
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$DIR/.." && pwd)"

PYTHON="python"
if [ -f "$ROOT_DIR/venv/bin/python" ]; then
    PYTHON="$ROOT_DIR/venv/bin/python"
elif [ -f "$ROOT_DIR/venv/Scripts/python.exe" ]; then
    PYTHON="$ROOT_DIR/venv/Scripts/python.exe"
fi

"$PYTHON" "$ROOT_DIR/scripts/switch_env.py" "$@"
