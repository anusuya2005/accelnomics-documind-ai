#!/usr/bin/env bash
# Does everything: checks programs, offers to install missing ones (Homebrew), sets up, starts.
# Run:  bash run_all.sh
cd "$(dirname "$0")" || exit 1

need_python() { command -v python3 >/dev/null 2>&1 && python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"; }
MISSING=()
need_python                      || MISSING+=("python@3.13")
command -v node >/dev/null 2>&1  || MISSING+=("node")
command -v ollama >/dev/null 2>&1 || MISSING+=("ollama")

if [ ${#MISSING[@]} -gt 0 ]; then
  echo "Missing or too old: ${MISSING[*]}"
  if command -v brew >/dev/null 2>&1; then
    read -r -p "Install them now with Homebrew? (y/n) " ANSWER
    case "$ANSWER" in
      [Yy]*) brew install "${MISSING[@]}" || { echo "STOP: Homebrew could not install them."; exit 1; } ;;
      *) echo "Cancelled. Install them and run this again."; exit 1 ;;
    esac
    hash -r
  else
    echo "Please install: Python 3.11+ (python.org), Node.js LTS (nodejs.org), Ollama (ollama.com)."
    echo "Then run this again. (With Homebrew, you could run: brew install ${MISSING[*]})"
    exit 1
  fi
  need_python && command -v node >/dev/null && command -v ollama >/dev/null \
    || { echo "Installed, but this window cannot see them yet. Close the window, open a new Terminal, and run this again."; exit 1; }
fi

if [ ! -x .venv/bin/python ] || [ ! -d frontend/node_modules ]; then
  bash setup.sh || exit 1
fi

if [ ! -f data/privatedocs.db ]; then
  bash start.sh --reset
else
  bash start.sh
fi
