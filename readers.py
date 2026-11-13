from pathlib import Path
from pypdf import PdfReader
from docx import Document


class ExtractionError(Exception):
    """The file could not be read, or has no text."""


def read_pdf(path):
    units = []
    for number, page in enumerate(PdfReader(path).pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            units.append((f"p. {number}", text))
    return units


def read_docx(path):
    units = []
    for number, para in enumerate(Document(path).paragraphs, start=1):
        text = para.text.strip()
        if text:
            units.append((f"¶ {number}", text))
    return units


def read_txt(path):
    units = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for number, line in enumerate(f, start=1):
            if line.strip():
                units.append((f"line {number}", line.strip()))
    return units


READERS = {".pdf": read_pdf, ".docx": read_docx, ".txt": read_txt}


def read_document(path):
    suffix = Path(path).suffix.lower()
    if suffix not in READERS:
        raise ExtractionError("Only PDF, DOCX and TXT files are supported.")
    try:
        units = READERS[suffix](path)
    except Exception as exc:
        raise ExtractionError(f"Could not read this file: {exc}") from exc
    if not units:
        raise ExtractionError("No text found. If this is a scanned PDF, it needs OCR.")
    return units
