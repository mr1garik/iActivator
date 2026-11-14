#!/bin/bash
# Build iActivator.app for macOS (run on a Mac).
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -c constraints.txt
.venv/bin/python build.py  # options and exclusions: see build.py
echo "Done: dist/iActivator.app"
