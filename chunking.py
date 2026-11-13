import re


def split_sentences(text):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [" ".join(s.split()) for s in sentences if s.strip()]   # also turns line breaks into spaces


def make_chunks(units, size=1000, overlap=150):
    """units = [(location, text), ...]  ->  [{"text": ..., "location": ...}, ...]"""
    chunks = []
    current = []          # list of (location, sentence)
    length = 0
    added = 0             # sentences added since the last chunk was saved

    for location, text in units:
        for sentence in split_sentences(text):
            if current and length + len(sentence) + 1 > size:
                chunks.append(current)                      # chunk is full: save it
                tail, tail_len = [], 0
                for item in reversed(current):              # carry last sentences forward
                    if tail_len + len(item[1]) > overlap:
                        break
                    tail.insert(0, item)
                    tail_len += len(item[1]) + 1
                current, length, added = tail, tail_len, 0
            current.append((location, sentence))
            length += len(sentence) + 1
            added += 1

    if current and added:                                   # save the last chunk
        chunks.append(current)

    result = []
    for chunk in chunks:
        first, last = chunk[0][0], chunk[-1][0]
        result.append({
            "text": " ".join(s for _, s in chunk),
            "location": first if first == last else f"{first} to {last}",
        })
    return result
