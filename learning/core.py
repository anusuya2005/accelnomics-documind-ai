import httpx, math
from pathlib import Path
from readers import read_document
from chunking import make_chunks           # NEW (Phase 3)

OLLAMA = "http://127.0.0.1:11434"

def embed(texts):
    r = httpx.post(f"{OLLAMA}/api/embed",
                   json={"model": "nomic-embed-text", "input": texts}, timeout=120)
    r.raise_for_status()
    return r.json()["embeddings"]

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))

def ask_model(prompt):
    r = httpx.post(f"{OLLAMA}/api/chat", json={
        "model": "llama3.2:3b", "stream": False,
        "options": {"temperature": 0, "num_ctx": 4096},
        "messages": [
            {"role": "system", "content":
             "Answer ONLY using the sources. If the answer is not in them, say: I could not find this in the documents."},
            {"role": "user", "content": prompt}],
    }, timeout=300)
    r.raise_for_status()
    return r.json()["message"]["content"]

# 1. read and chunk (CHANGED in Phase 3)
FILE = "sample.pdf"
units = read_document(FILE)
if Path(FILE).suffix.lower() == ".pdf":
    groups = [[u] for u in units]          # PDF: chunk each page separately, never mix pages
else:
    groups = [units]
chunk_list = [c for g in groups for c in make_chunks(g, size=1000, overlap=150)]
chunks = [c["text"] for c in chunk_list]
locations = [c["location"] for c in chunk_list]
print(f"Indexed {len(chunks)} chunks from {FILE}")

# 2. embed every chunk
vectors = embed(["search_document: " + c for c in chunks])

# 3. ask questions in a loop
while True:
    q = input("\nQuestion (or 'quit'): ").strip()
    if q == "quit":
        break
    qv = embed(["search_query: " + q])[0]
    scored = sorted(
        ((cosine(qv, v), c, loc) for v, c, loc in zip(vectors, chunks, locations)),
        reverse=True)[:3]                  # CHANGED: top 3 now
    for score, c, loc in scored:
        print(f"  match {score:.2f} ({loc}): {c[:70]}")
    sources = "\n".join(f"[S{i+1}] {c}" for i, (_, c, _) in enumerate(scored))
    print("\nAnswer:", ask_model(f"Sources:\n{sources}\n\nQuestion: {q}"))
