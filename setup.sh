#!/bin/bash
set -e
echo "[SETUP] huh project — redwood"
PYTHON="${PYTHON:-python3}"
$PYTHON --version
echo "[SETUP] Loading binaries..."
$PYTHON loader.py load
echo "[SETUP] Done. Run: $PYTHON loader.py test"
