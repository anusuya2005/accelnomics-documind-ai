from ollama_client import embed
from permissions import allowed_department_ids
from vector_store import collection

MIN_SIMILARITY = 0.35     # absolute floor
RELATIVE_MARGIN = 0.10    # keep only chunks within 0.10 of the best match
MAX_SOURCES = 5


def retrieve(conn, user, question):
    allowed = allowed_department_ids(conn, user)              # read from the database, every time
    if not allowed or collection.count() == 0:
        return []                                             # nothing to search, so do not search

    vector = embed(["search_query: " + question])[0]
    found = collection.query(
        query_embeddings=[vector],
        n_results=min(8, collection.count()),
        where={"department_id": {"$in": allowed}},            # permission filter INSIDE the search
    )

    hits = []
    for text, meta, distance in zip(found["documents"][0], found["metadatas"][0], found["distances"][0]):
        doc = conn.execute("SELECT display_name, department_id, status FROM documents WHERE id = ?",
                           (meta["doc_id"],)).fetchone()
        # Second check, in the database that is the source of truth. Fail closed.
        if doc is None or doc["status"] != "indexed" or doc["department_id"] not in allowed:
            continue
        similarity = 1 - distance
        if similarity < MIN_SIMILARITY:
            continue
        hits.append({
            "document_id": meta["doc_id"],
            "document": doc["display_name"],
            "location": meta["location"],
            "text": text,
            "similarity": round(similarity, 3),
        })

    if not hits:
        return []
    best = hits[0]["similarity"]                              # results arrive best first
    hits = [h for h in hits if h["similarity"] >= best - RELATIVE_MARGIN][:MAX_SOURCES]
    for i, h in enumerate(hits, start=1):
        h["label"] = f"S{i}"                                  # labels are given AFTER filtering
    return hits
