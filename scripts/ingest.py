"""Build the local sqlite-vec literature database from PDFs in data/pdfs/."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Any

import sqlite_vec
from pypdf import PdfReader

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import DATABASE_PATH, PDF_DIR
from app.rag import EMBEDDING_MODEL_NAME

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def split_words(text: str) -> list[str]:
    """Split text into approximately 500-word overlapping chunks."""
    words = text.split()
    if not words:
        return []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    return [" ".join(words[start : start + CHUNK_SIZE]) for start in range(0, len(words), step)]


def page_chunks(pdf_path: Path) -> list[tuple[str, int, str]]:
    """Extract non-empty chunks with their original PDF page number."""
    reader = PdfReader(str(pdf_path))
    chunks: list[tuple[str, int, str]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        for text in split_words(page.extract_text() or ""):
            chunks.append((pdf_path.name, page_number, text))
    return chunks


def _connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.enable_load_extension(True)
    sqlite_vec.load(connection)
    connection.enable_load_extension(False)
    return connection


def ingest() -> int:
    """Rebuild the local corpus atomically, so reruns never duplicate chunks."""
    pdf_paths = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_paths:
        raise RuntimeError(f"No PDF files found in {PDF_DIR}")
    chunks = [chunk for pdf_path in pdf_paths for chunk in page_chunks(pdf_path)]
    if not chunks:
        raise RuntimeError("No extractable PDF text was found.")

    from sentence_transformers import SentenceTransformer

    model: Any = SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)
    embeddings = model.encode(
        [chunk[2] for chunk in chunks], normalize_embeddings=True, show_progress_bar=True
    )
    with _connection() as connection:
        connection.execute("DROP TABLE IF EXISTS vec_chunks")
        connection.execute("DROP TABLE IF EXISTS chunks")
        connection.execute(
            """CREATE TABLE chunks (
                id INTEGER PRIMARY KEY,
                doc_name TEXT NOT NULL,
                page INTEGER NOT NULL,
                text TEXT NOT NULL
            )"""
        )
        connection.execute(
            "CREATE VIRTUAL TABLE vec_chunks USING vec0(embedding float[384])"
        )
        for (doc_name, page, text), embedding in zip(chunks, embeddings, strict=True):
            cursor = connection.execute(
                "INSERT INTO chunks (doc_name, page, text) VALUES (?, ?, ?)",
                (doc_name, page, text),
            )
            connection.execute(
                "INSERT INTO vec_chunks (rowid, embedding) VALUES (?, ?)",
                (cursor.lastrowid, sqlite_vec.serialize_float32(embedding.tolist())),
            )
    return len(chunks)


if __name__ == "__main__":
    print(f"Indexed {ingest()} chunks into {DATABASE_PATH}")
