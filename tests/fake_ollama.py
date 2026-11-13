"""A pretend Ollama. Tests never talk to the real model, so they are fast, free and repeatable."""
import hashlib
import math
import re

STOP = set("a an the is are was were be to of in on at for and or what how many do does did my our i it "
           "this that with from by as can you your we".split())
DIMS = 2048
calls = []               # every chat call is recorded here: [{"system":..., "user":...}]
forced_reply = [None]    # a test can set forced_reply[0] = "text" to make the model "misbehave"


def words(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


def embed_one(text):
    vec = [0.0] * DIMS
    for w in words(text.replace("search_query:", "").replace("search_document:", "")):
        vec[int(hashlib.md5(w.encode()).hexdigest(), 16) % DIMS] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def fake_chat(user_prompt):
    question = next((l.split(":", 1)[1] for l in user_prompt.split("\n") if l.upper().startswith("QUESTION:")), "")
    q = set(words(question))
    best, best_score = None, 0
    for line in user_prompt.split("\n"):
        m = re.match(r"\[(S\d+)\] (.*)", line)
        if not m:
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", m.group(2)):
            score = len(q & set(words(sentence)))
            if score > best_score:
                best, best_score = (m.group(1), sentence), score
    if best is None or best_score < 2:
        return "Not stated in the documents."
    return f"According to [{best[0]}], {best[1]}"


def fake_post(path, payload, timeout):
    if path == "/api/embed":
        return {"embeddings": [embed_one(t) for t in payload["input"]]}
    if path == "/api/chat":
        system, user = payload["messages"][0]["content"], payload["messages"][1]["content"]
        calls.append({"system": system, "user": user})
        reply = forced_reply[0] if forced_reply[0] is not None else fake_chat(user)
        return {"message": {"content": reply}}
    raise AssertionError(f"unexpected Ollama call: {path}")
