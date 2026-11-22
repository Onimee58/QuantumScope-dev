#!/usr/bin/env bash
set -Eeuo pipefail

# QuantumScope v0.1.2: install dependencies, create venv, and launch GUI.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f pyproject.toml ]]; then
  echo "Error: Put install_and_run.sh inside the QuantumScope project folder (next to pyproject.toml)." >&2
  exit 1
fi

# v1.0.1: a Python from conda/Anaconda brings its own graphics libraries, which can stop Qt's OpenGL
# ("Could not initialize GLX"). When a conda environment is active, use the system's Python instead.
PYTHON=python3
is_conda_python() {
  "$1" -c 'import sys, os; p = sys.base_prefix.lower(); sys.exit(0 if ("conda" in p or os.path.isdir(os.path.join(sys.base_prefix, "conda-meta"))) else 1)' 2>/dev/null
}
if command -v python3 >/dev/null 2>&1 && is_conda_python python3; then
  if [[ -x /usr/bin/python3 ]] && /usr/bin/python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'; then
    PYTHON=/usr/bin/python3
    echo "Note: a conda environment is active; using the system Python ($PYTHON) for QuantumScope."
  else
    echo "Warning: only a conda Python was found. If QuantumScope fails with 'Could not initialize GLX'," >&2
    echo "         run 'conda deactivate', install python3 (3.11 or newer) with your package manager, and try again." >&2
  fi
fi

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Error: python3 is not installed." >&2
  exit 1
fi

if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' ; then
  echo "Error: Python 3.11 or newer is required." >&2
  exit 1
fi

if command -v apt-get >/dev/null 2>&1; then
  echo "[1/4] Installing Ubuntu/Debian system libraries (sudo may ask for your password)..."
  sudo apt-get update
  sudo apt-get install -y python3-venv python3-pip libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0
else
  echo "[1/4] Skipping apt dependencies (not an apt-based Linux distribution)."
  echo "       Install Python venv, OpenGL, EGL and X11/Qt runtime libraries with your package manager."
fi

if [[ -x .venv/bin/python && "$PYTHON" != python3 ]] && is_conda_python .venv/bin/python; then
  echo "[2/4] The existing .venv was made from a conda Python: making it again from $PYTHON..."
  rm -rf .venv
fi
if [[ ! -x .venv/bin/python ]]; then
  echo "[2/4] Creating local Python environment..."
  "$PYTHON" -m venv .venv
else
  echo "[2/4] Reusing existing .venv"
fi

echo "[3/4] Installing QuantumScope and Python dependencies..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'

if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  echo "Warning: No graphical display was detected. The GUI may not launch in a headless session." >&2
fi

echo "[4/4] Launching QuantumScope..."
exec .venv/bin/quantumscope
