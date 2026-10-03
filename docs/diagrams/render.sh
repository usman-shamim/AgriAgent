#!/usr/bin/env bash
# Render docs/diagrams/*.mmd to SVG/PNG, rebuild interactive.html, and verify the
# README embeds are still in sync. All logic lives in build.py.
set -euo pipefail

exec python3 "$(dirname "$0")/build.py" "$@"
