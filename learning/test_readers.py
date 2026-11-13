from readers import read_document

for name in ["notes.txt", "sample.pdf", "sample.docx"]:
    units = read_document(name)
    print(f"\n{name}: {len(units)} pieces")
    for location, text in units[:3]:
        print(f"  {location}: {text[:60]}")
