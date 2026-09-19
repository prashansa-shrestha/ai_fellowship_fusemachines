"""Chunk + embed + FAISS retrieval for the course corpus (.txt / .pdf)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable, List, NamedTuple, Optional

import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

from . import config


class Chunk(NamedTuple):
    text: str
    source: str


def _load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_pdf(path: Path) -> str:
    pages = PdfReader(str(path)).pages
    return "\n".join(p.extract_text() or "" for p in pages)


def load_documents(corpus_dir: Path) -> List[tuple[str, str]]:
    """(filename, body) for each ingestible file under corpus_dir."""
    out: List[tuple[str, str]] = []
    for path in sorted(corpus_dir.iterdir()):
        ext = path.suffix.lower()
        if ext == ".txt":
            out.append((path.name, _load_txt(path)))
        elif ext == ".pdf":
            out.append((path.name, _load_pdf(path)))
    return out


def extract_week_filter(query: str) -> Optional[Callable[[str], bool]]:
    """If the user names a week, restrict retrieval to that week's files.

    Short embeddings bury the week number under body text, so pure semantic
    search often misses "Week N" questions. Keyword filter first, then rank.
    """
    m = re.search(r"week\s*#?\s*(\d+)", query, re.IGNORECASE)
    if m is None:
        return None
    prefix = f"Week_{m.group(1)}_"
    return lambda src: src.startswith(prefix)


def chunk_text(text: str, source: str, chunk_size: int, overlap: int) -> List[Chunk]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    pieces: List[Chunk] = []
    i = 0
    n = len(cleaned)
    while i < n:
        j = i + chunk_size
        pieces.append(Chunk(text=cleaned[i:j], source=source))
        if j >= n:
            break
        i = j - overlap
    return pieces


class RagIndex:
    def __init__(self, embedding_model: str = config.EMBEDDING_MODEL):
        self.model = SentenceTransformer(embedding_model)
        self.index: faiss.Index | None = None
        self.chunks: List[Chunk] = []
        # Keep raw vectors so we can score a week-filtered subset without FAISS filters.
        self.embeddings: np.ndarray | None = None

    def build(self, corpus_dir: Path, chunk_size: int, overlap: int) -> None:
        pieces: List[Chunk] = []
        for name, body in load_documents(corpus_dir):
            pieces.extend(chunk_text(body, name, chunk_size, overlap))

        if not pieces:
            raise ValueError(f"No ingestible documents found in {corpus_dir}")

        vecs = self.model.encode([c.text for c in pieces], normalize_embeddings=True)
        vecs = np.asarray(vecs, dtype="float32")

        faiss_index = faiss.IndexFlatIP(vecs.shape[1])
        faiss_index.add(vecs)

        self.index = faiss_index
        self.chunks = pieces
        self.embeddings = vecs

    def save(self, index_dir: Path) -> None:
        index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(index_dir / "index.faiss"))
        np.save(index_dir / "embeddings.npy", self.embeddings)
        payload = [{"text": c.text, "source": c.source} for c in self.chunks]
        (index_dir / "chunks.json").write_text(json.dumps(payload))

    def load(self, index_dir: Path) -> None:
        self.index = faiss.read_index(str(index_dir / "index.faiss"))
        self.embeddings = np.load(index_dir / "embeddings.npy")
        raw = json.loads((index_dir / "chunks.json").read_text())
        self.chunks = [Chunk(**row) for row in raw]

    def search(self, query: str, top_k: int = config.TOP_K) -> List[Chunk]:
        q = self.model.encode([query], normalize_embeddings=True)
        q = np.asarray(q, dtype="float32")

        week_pred = extract_week_filter(query)
        if week_pred is not None:
            idxs = [i for i, c in enumerate(self.chunks) if week_pred(c.source)]
            if idxs:
                scores = self.embeddings[idxs] @ q[0]
                ordered = sorted(zip(idxs, scores), key=lambda pair: -pair[1])[:top_k]
                return [self.chunks[i] for i, _ in ordered]
            # Unknown week number — fall back to open semantic search.

        _, ids = self.index.search(q, top_k)
        return [self.chunks[i] for i in ids[0] if i != -1]
