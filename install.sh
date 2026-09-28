#!/usr/bin/env bash
# Sets up a virtualenv and installs Python dependencies for the CubeSat Simulator.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

PYTHON="${PYTHON:-python3}"
VENV_DIR="$PROJECT_ROOT/.venv"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Error: $PYTHON not found. Install Python 3.11+ or set PYTHON=/path/to/python3." >&2
    exit 1
fi

if [ -d "$VENV_DIR" ]; then
    echo "Virtualenv already exists at $VENV_DIR, reusing it."
else
    echo "Creating virtualenv at $VENV_DIR..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing Python dependencies from requirements.txt..."
pip install -r "$PROJECT_ROOT/requirements.txt"

echo
echo "Python dependencies installed."
echo

# jpype/Orekit need a real JVM (a JDK), which pip can't provide.
echo "Checking for a Java installation (required by jpype/Orekit)..."
if [ -n "${JAVA_HOME:-}" ] && [ ! -d "$JAVA_HOME" ]; then
    echo "⚠️  JAVA_HOME is set to a path that doesn't exist: $JAVA_HOME"
    echo "    This overrides auto-detection and will break the JVM even if a JDK is installed."
    echo "    Fix or remove it from your shell profile (~/.zshrc, ~/.bash_profile)."
fi

java_found=0
if [[ "$OSTYPE" == "darwin"* ]] && command -v /usr/libexec/java_home >/dev/null 2>&1; then
    if detected_java_home="$(/usr/libexec/java_home 2>/dev/null)"; then
        java_found=1
        echo "Found JDK: $detected_java_home"
    fi
elif command -v java >/dev/null 2>&1; then
    java_found=1
    echo "Found java on PATH: $(command -v java)"
fi

if [ "$java_found" -eq 0 ]; then
    echo "No Java installation found. Attempting to install a JDK..."
    if [[ "$OSTYPE" == "darwin"* ]] && command -v brew >/dev/null 2>&1; then
        brew install --cask temurin
        java_found=1
    elif command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y openjdk-17-jdk
        java_found=1
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y java-17-openjdk-devel
        java_found=1
    else
        echo "⚠️  Could not auto-install Java: no supported package manager (brew/apt-get/dnf) found." >&2
        echo "    Install a JDK manually (e.g. https://adoptium.net/) before running the simulator." >&2
    fi
fi
echo

# Orekit jars/data can't be installed via pip; check whether they're already in place.
JAR_DIR="$HOME/Orekit-Jars"
DATA_DIR="$HOME/orekit-data"

missing=0
if [ ! -d "$JAR_DIR" ] || [ -z "$(ls -A "$JAR_DIR" 2>/dev/null)" ]; then
    missing=1
    echo "⚠️  Orekit jars not found at $JAR_DIR"
fi
if [ ! -d "$DATA_DIR" ] || [ -z "$(ls -A "$DATA_DIR" 2>/dev/null)" ]; then
    missing=1
    echo "⚠️  Orekit data not found at $DATA_DIR"
fi

if [ "$missing" -eq 1 ]; then
    cat <<'EOF'

Remaining manual setup required before running the simulator:
  1. Download the Orekit + Hipparchus jar files and place them in ~/Orekit-Jars
     (hipparchus-*.jar and orekit-*.jar — see https://www.orekit.org/)
  2. Download the Orekit data archive and extract it to ~/orekit-data
     (https://gitlab.orekit.org/orekit/orekit-data)

Once those are in place, launch the simulator with ./run.sh
EOF
else
    echo "Orekit jars and data found. Setup complete — launch the simulator with ./run.sh"
fi
