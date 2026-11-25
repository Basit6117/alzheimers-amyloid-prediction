"""Educational RAG path; deliberately independent from prediction code."""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import sqlite_vec

from app.config import (
    DATABASE_PATH,
    GEMINI_API_KEY,
    GEMINI_FALLBACK_MODEL,
    GEMINI_MODEL,
    GEMINI_RETRY_ATTEMPTS,
    GEMINI_TIMEOUT_SECONDS,
    RAG_MAX_DISTANCE,
    RAG_TOP_K,
)

NO_MATCH_REPLY = "I couldn't find this in the loaded literature."
GENERAL_GEMINI_PREFIX = "General Gemini information (not from the loaded literature): "
PERSONAL_DIAGNOSIS_REPLY = (
    "I can't diagnose or interpret personal results. Please use the diagnostic "
    "tool for its screening output and discuss it with a qualified clinician."
)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
logger = logging.getLogger("uvicorn.error")


class RagUnavailableError(RuntimeError):
    """Raised when the local corpus or Gemini cannot serve a chat answer."""


@dataclass(frozen=True)
class RetrievedChunk:
    doc: str
    page: int
    text: str
    distance: float


if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


_embedding_model: Any | None = None


def _embedding_model_instance() -> Any:
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer

        _embedding_model = SentenceTransformer(
            EMBEDDING_MODEL_NAME, local_files_only=True
        )
    return _embedding_model


def _connect() -> sqlite3.Connection:
    if not DATABASE_PATH.exists():
        raise RagUnavailableError("The literature database has not been created.")
    connection = sqlite3.connect(DATABASE_PATH)
    connection.enable_load_extension(True)
    sqlite_vec.load(connection)
    connection.enable_load_extension(False)
    return connection


def _is_personal_diagnosis_request(message: str) -> bool:
    lowered = message.casefold()
    personal_terms = ("my result", "my risk", "my score", "my number", "my values", "do i have", "am i")
    interpretation_terms = ("diagnos", "interpret", "risk", "positive", "negative", "alzheimer")
    return any(term in lowered for term in personal_terms) and any(
        term in lowered for term in interpretation_terms
    )


def retrieve(question: str, top_k: int = RAG_TOP_K) -> list[RetrievedChunk]:
    """Return local PDF chunks within the configured normalized-vector distance."""
    embedding = _embedding_model_instance().encode(
        [question], normalize_embeddings=True
    )[0]
    with _connect() as connection:
        serialized = sqlite_vec.serialize_float32(embedding.tolist())
        rows = connection.execute(
            """
            SELECT chunks.doc_name, chunks.page, chunks.text, vec_chunks.distance
            FROM vec_chunks
            JOIN chunks ON chunks.id = vec_chunks.rowid
            WHERE vec_chunks.embedding MATCH ? AND k = ?
            ORDER BY vec_chunks.distance
            """,
            (serialized, top_k),
        ).fetchall()
    return [
        RetrievedChunk(doc=row[0], page=int(row[1]), text=row[2], distance=float(row[3]))
        for row in rows
        if float(row[3]) <= RAG_MAX_DISTANCE
    ]


def _generate_with_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise RagUnavailableError("GEMINI_API_KEY is not configured.")

    request_body = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 500,
                "temperature": 0.2,
                "thinkingConfig": {"thinkingLevel": "low"},
            },
        }
    ).encode("utf-8")
    payload: dict[str, Any] | None = None
    models = tuple(dict.fromkeys((GEMINI_MODEL, GEMINI_FALLBACK_MODEL)))
    for model_index, model_name in enumerate(models):
        request = Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent",
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY,
            },
            method="POST",
        )
        for attempt in range(GEMINI_RETRY_ATTEMPTS):
            try:
                with urlopen(request, timeout=GEMINI_TIMEOUT_SECONDS) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except HTTPError as error:
                retryable = error.code in {429, 500, 502, 503, 504}
                logger.warning("Gemini model %s failed with HTTP %s", model_name, error.code)
                if not retryable:
                    raise RagUnavailableError("Gemini is unavailable. Please try again later.") from error
                if attempt + 1 < GEMINI_RETRY_ATTEMPTS:
                    time.sleep(attempt + 1)
            except (URLError, TimeoutError) as error:
                logger.warning("Gemini model %s had a network or timeout error", model_name)
                if attempt + 1 < GEMINI_RETRY_ATTEMPTS:
                    time.sleep(attempt + 1)
        if payload is not None:
            break
        if model_index + 1 < len(models):
            logger.info("Falling back from Gemini model %s", model_name)

    if payload is None:
        raise RagUnavailableError("Gemini is unavailable. Please try again later.")
    try:
        return str(payload["candidates"][0]["content"]["parts"][0]["text"]).strip()
    except (IndexError, KeyError, TypeError) as error:
        raise RagUnavailableError("Gemini returned an unusable response.") from error


def _gemini_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    """Answer strictly from retrieved PDF chunks."""
    context = "\n\n".join(
        f"[Source: {chunk.doc}, page {chunk.page}]\n{chunk.text}" for chunk in chunks
    )
    prompt = (
        "Answer the user's educational question using only the supplied literature "
        "context. Do not diagnose, predict risk, interpret personal numbers, or add "
        "facts not supported by the context. If the context does not answer the "
        "question, say exactly: I couldn't find this in the loaded literature.\n\n"
        f"Literature context:\n{context}\n\nUser question: {question}"
    )
    return _generate_with_gemini(prompt)


def _gemini_general_answer(question: str) -> str:
    """Answer a general educational question without claiming PDF support."""
    prompt = (
        "Give a concise, general educational answer about Alzheimer's disease or "
        "related biomarkers. This answer is not supported by the local literature, "
        "so do not cite or imply a source. Do not diagnose, predict risk, interpret "
        "personal numbers, or provide medical advice. If the question asks for a "
        "personal diagnosis or treatment decision, say that a qualified clinician "
        "should be consulted.\n\n"
        f"User question: {question}"
    )
    return _generate_with_gemini(prompt)


def answer_question(message: str) -> tuple[str, list[dict[str, str | int]]]:
    """Answer from local retrieval, with fixed safety and no-match responses."""
    if _is_personal_diagnosis_request(message):
        return PERSONAL_DIAGNOSIS_REPLY, []
    chunks = retrieve(message)
    if not chunks:
        return GENERAL_GEMINI_PREFIX + _gemini_general_answer(message), []
    answer = _gemini_answer(message, chunks)
    if answer == NO_MATCH_REPLY:
        return GENERAL_GEMINI_PREFIX + _gemini_general_answer(message), []
    sources = [{"doc": chunk.doc, "page": chunk.page} for chunk in chunks]
    return answer, sources
