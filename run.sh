#!/usr/bin/env bash
# Starts the CubeSat Simulator GUI.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR="$PROJECT_ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
if [ ! -x "$VENV_PYTHON" ]; then
    echo "Error: virtualenv not found at $VENV_DIR" >&2
    echo "Create it with: ./install.sh" >&2
    exit 1
fi

if [ ! -d "$HOME/Orekit-Jars" ]; then
    echo "Error: Orekit jars not found at $HOME/Orekit-Jars" >&2
    exit 1
fi
if [ ! -d "$HOME/orekit-data" ]; then
    echo "Error: Orekit data not found at $HOME/orekit-data" >&2
    exit 1
fi

exec "$VENV_PYTHON" -m simulator.main
