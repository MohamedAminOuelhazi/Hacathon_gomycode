import re
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).resolve().parents[2] / "data" / "documents"
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150


def _chunks(text: str):
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        yield text[start:end]
        if end == len(text):
            break
        start = end - CHUNK_OVERLAP


def search_company_documents(query: str) -> dict:
    terms = set(re.findall(r"[\w'-]+", query.lower()))
    if not terms:
        return {"results": []}
    results = []
    if not DOCUMENTS_DIR.exists():
        return {"results": []}

    for path in sorted(DOCUMENTS_DIR.rglob("*.md")):
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for chunk in _chunks(content):
            words = set(re.findall(r"[\w'-]+", chunk.lower()))
            score = len(terms & words) / len(terms)
            if score > 0:
                results.append({
                    "document": path.relative_to(DOCUMENTS_DIR).as_posix(),
                    "content": chunk.strip(),
                    "relevance": round(score, 3),
                })
    results.sort(key=lambda item: item["relevance"], reverse=True)
    return {"results": results[:5]}
