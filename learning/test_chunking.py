from chunking import make_chunks

text = " ".join(f"This is sentence number {i} about the company policy." for i in range(1, 60))
chunks = make_chunks([("line 1", text)], size=300, overlap=80)

print("chunks:", len(chunks))
for i, c in enumerate(chunks):
    print(f"\n--- chunk {i} ({len(c['text'])} chars) ---")
    print(c["text"])
