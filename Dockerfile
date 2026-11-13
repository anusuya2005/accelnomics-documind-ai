# Accelnomics DocuMind AI: the app (backend + built website). Ollama runs in its own container.
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Only the application files are copied, never notes, passwords or test data.
COPY main.py database.py answering.py retrieval.py privacy.py ollama_client.py security.py \
     permissions.py readers.py chunking.py vector_store.py set_password.py create_user.py ./
COPY --from=web /web/dist ./frontend/dist

# Run as a normal user, not root. All data lives in /app/data (a Docker volume).
RUN useradd --create-home app && mkdir -p /app/data && chown -R app:app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/login-options')"
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
