#!/usr/bin/env bash
# One-time setup for PrivateDocs AI on Mac (also works on Linux). Run:  bash setup.sh
cd "$(dirname "$0")" || exit 1

fail() { echo; echo "STOP: $1"; exit 1; }

# 1. Programs that must already be installed
command -v python3 >/dev/null 2>&1 || fail "'python3' was not found. Install it from python.org (or: brew install python)."
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" \
  || fail "Python 3.11 or newer is needed. Your 'python3' is older. Install it from python.org (or: brew install python)."
command -v node >/dev/null 2>&1   || fail "'node' was not found. Install Node.js (LTS) from nodejs.org (or: brew install node)."
command -v npm >/dev/null 2>&1    || fail "'npm' was not found. Install Node.js (LTS) from nodejs.org (or: brew install node)."
command -v ollama >/dev/null 2>&1 || fail "'ollama' was not found. Install it from ollama.com (or: brew install ollama)."

# 2. Python environment and packages
if [ ! -x .venv/bin/python ]; then
  echo "Creating the Python environment..."
  python3 -m venv .venv || fail "Creating the Python environment failed."
fi
echo "Installing Python packages (a few minutes)..."
.venv/bin/python -m pip install -r requirements.txt || fail "Installing Python packages failed."

# 3. Website packages
echo "Installing website packages..."
(cd frontend && npm install) || fail "npm install failed."

# 4. Local AI models (names are read from the code, so they never go out of date)
if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Starting Ollama..."
  (ollama serve >/dev/null 2>&1 &)
  sleep 5
fi
CHAT=$(.venv/bin/python -c "import ollama_client; print(ollama_client.CHAT_MODEL)")
EMBED=$(.venv/bin/python -c "import ollama_client; print(ollama_client.EMBED_MODEL)")
echo "Downloading models $EMBED and $CHAT (several GB, only the first time)..."
ollama pull "$EMBED" || fail "Downloading $EMBED failed."
ollama pull "$CHAT"  || fail "Downloading $CHAT failed."

# 5. Quick self-test (uses a pretend AI model, so it is fast)
echo "Running the automatic tests..."
.venv/bin/python -m pytest tests -q || fail "The tests failed."

echo
echo "Setup finished. Next:  bash start.sh --reset   (first time, makes demo data)"
