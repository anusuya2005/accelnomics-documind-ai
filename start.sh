#!/usr/bin/env bash
# Starts PrivateDocs AI. Run:
#   bash start.sh --reset   first time: fresh demo data (asks you to choose ONE demo password)
#   bash start.sh           later: just start
# Press Ctrl+C in this window to stop everything.
cd "$(dirname "$0")" || exit 1
PY=.venv/bin/python
fail() { echo; echo "STOP: $1"; exit 1; }
[ -x "$PY" ] || fail "Run  bash setup.sh  first."

# Ollama must be running
if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Starting Ollama..."
  (ollama serve >/dev/null 2>&1 &)
  sleep 5
fi

# The ports must be free
for port in 8000 5173; do
  if curl -s "http://127.0.0.1:$port" >/dev/null 2>&1; then
    fail "Something already uses port $port. Is PrivateDocs AI already running in another window? Stop it first."
  fi
done

# Fresh demo data (asks for a password ONCE; the old data folder is kept as data_backup_...)
if [ "$1" = "--reset" ]; then
  read -r -s -p "Choose ONE password for all demo users (min 10 characters): " PD_DEMO_PASSWORD; echo
  export PD_DEMO_PASSWORD
  "$PY" reset_demo.py || fail "Reset failed. Nothing else was started."
fi

# Backend and website in the background of this window
"$PY" -m uvicorn main:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
BACK=$!
(cd frontend && exec ./node_modules/.bin/vite --host 127.0.0.1 --port 5173 > ../website.log 2>&1) &
FRONT=$!
cleanup() { kill "$BACK" "$FRONT" 2>/dev/null; }
trap cleanup EXIT INT TERM

# Wait until the backend answers
for _ in $(seq 1 60); do
  curl -s http://127.0.0.1:8000/docs >/dev/null 2>&1 && break
  kill -0 "$BACK" 2>/dev/null || fail "The backend stopped. Read backend.log"
  sleep 1
done
curl -s http://127.0.0.1:8000/docs >/dev/null 2>&1 || fail "The backend did not start. Read backend.log"

# First time: load the demo documents
if [ "$1" = "--reset" ]; then
  "$PY" load_docs.py
  unset PD_DEMO_PASSWORD
fi

sleep 2
(command -v open >/dev/null 2>&1 && open http://127.0.0.1:5173) || (command -v xdg-open >/dev/null 2>&1 && xdg-open http://127.0.0.1:5173) || true
echo
echo "Ready: http://127.0.0.1:5173   (sign in as admin1, hr_anu, it_ravi or fin_meena)"
echo "Leave this window open. Press Ctrl+C to stop."
wait
