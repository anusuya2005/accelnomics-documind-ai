# Accelnomics DocuMind AI

A privacy-first document assistant. Staff ask questions in plain English and get answers written only from their company's own documents, with the exact source shown beside every answer. The AI model and all data run on one computer. Nothing is sent to the internet.

> **This is a prototype for learning and review, not a product for real company use.** All demo documents are fictional. It is not security-certified.

## What it does

- Answers questions from PDF, DOCX and TXT documents (retrieval-augmented generation).
- Shows the source page next to each answer, with the matching sentences highlighted.
- Says "Not found in your documents" instead of guessing.
- Keeps each department's documents separate (HR, IT, Finance). The server enforces this.
- Admin pages: Documents (upload, delete), Privacy (live checks) and Audit log (events only, never questions or answers).
- Passwords are stored as Argon2 hashes, sessions expire after 8 hours, and 5 wrong passwords lock an account for 15 minutes.

## Tech stack

| Part | Technology |
| --- | --- |
| Frontend | React 19, TypeScript, Vite |
| Backend | Python, FastAPI, Uvicorn |
| Chat model | Ollama, `gemma3:latest` |
| Search model | Ollama, `nomic-embed-text` |
| Search storage | ChromaDB (local folder) |
| Records | SQLite (users, documents, sessions, audit log) |
| Tests | pytest (86 tests) and a 20-question evaluation |

## How it works

1. **Upload (admin):** read the file, split it into pieces of about 1000 characters, remove sentences that try to give orders to the AI, turn each piece into numbers (an embedding), and store it with its department.
2. **Ask (staff):** turn the question into numbers, find the closest pieces from only that person's departments, re-check access in the database, let the local model write an answer from those pieces only, then have the server check the answer and build the source list.

## Requirements (Windows)

- Python 3.11 or newer
- Node.js 20 or newer (only to build the frontend)
- [Ollama](https://ollama.com) with two models:

```powershell
ollama pull gemma3
ollama pull nomic-embed-text
```

## Setup

```powershell
git clone https://github.com/anusuya2005/accelnomics-documind-ai.git
cd accelnomics-documind-ai
# 1. Python environment and libraries
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# 2. Build the frontend
cd frontend
npm install
npm run build
cd ..
```

Then create an admin and a staff user (the script asks for a password; `--keep-password` skips the forced change at first login):

```powershell
python create_user.py admin1 --role admin --keep-password
python create_user.py staff1 --role staff --dept HR --keep-password
```

## Run

```powershell
.\start_app.ps1
```

Open `http://127.0.0.1:8000`. The first answer can take up to about 40 seconds on a laptop because the model runs locally.

## Load the demo documents

1. Start the app (`.\start_app.ps1`) and wait about a minute.
2. In a second terminal, in the same folder, run `.venv\Scripts\Activate.ps1` and then:

```powershell
python load_docs.py
```

Enter the `admin1` password when asked. The eight fictional files in `docs/` are uploaded to HR, IT and Finance and indexed. Then sign in at `http://127.0.0.1:8000`. Try `staff1` (HR only) to see that other departments' documents are not visible.

## Tests

```powershell
python -m pytest tests -q          # 86 tests
python eval\run_eval.py questions_bank.json   # 20-question evaluation (the app must be running)
```

## What is not in this repository

The `data` folder (SQLite database, ChromaDB search index, uploaded files), `.venv`, `node_modules`, logs and passwords are not stored here. They are created on your computer when you run the app and add documents. The AI models come from Ollama (`ollama pull`).

Open a new terminal each time you work on the project and run `.venv\Scripts\Activate.ps1` first.

## Project files

| File | Job |
| --- | --- |
| `main.py` | API routes and login checks |
| `security.py` | Password hashing and sessions |
| `database.py` | SQLite records |
| `readers.py`, `chunking.py` | Read PDF, DOCX, TXT and split into pieces |
| `ollama_client.py` | Talks to the local models |
| `vector_store.py` | ChromaDB storage and search |
| `retrieval.py`, `permissions.py` | Find pieces and enforce department access |
| `answering.py` | Writes the answer and builds the citations |
| `frontend/` | React website |
| `tests/`, `eval/` | Automated tests and the 20-question evaluation |

## Known limits and next steps

- Fictional data only. Not security-certified. Plain `http` on one computer.
- Users are created by a command. An admin Users page, forced first-login password change, HTTPS and single sign-on are planned next.
- About 40 seconds per answer on a laptop. Streaming answers and a stronger computer would help.
- The evaluation has 20 questions, which is a small sample.
- Scanned (image-only) PDFs are not tested.

## Author

Anusuya V, final-year B.Tech Information Technology.

Note: 4 website tests are skipped until the frontend is built with `npm run build`.
