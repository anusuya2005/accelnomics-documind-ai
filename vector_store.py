import chromadb
from chromadb.config import Settings

TELEMETRY = False        # no usage reports. The Privacy Console reads this same value.

_client = chromadb.PersistentClient(
    path="data/chroma",
    settings=Settings(anonymized_telemetry=TELEMETRY),
)
collection = _client.get_or_create_collection(
    "chunks",
    metadata={"hnsw:space": "cosine"},               # similarity = 1 - distance
    embedding_function=None,                         # never let Chroma download its own embedder
)
