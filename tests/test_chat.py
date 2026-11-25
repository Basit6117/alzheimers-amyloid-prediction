"""Safety and contract tests for the isolated educational chat endpoint."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.rag import (
    GENERAL_GEMINI_PREFIX,
    NO_MATCH_REPLY,
    PERSONAL_DIAGNOSIS_REPLY,
    answer_question,
)


def test_personal_diagnosis_request_never_retrieves_or_calls_gemini(monkeypatch) -> None:
    def retrieval_must_not_run(_: str):
        raise AssertionError("Personal diagnosis request reached retrieval")

    monkeypatch.setattr("app.rag.retrieve", retrieval_must_not_run)

    answer, sources = answer_question("Can you interpret my risk score?")

    assert answer == PERSONAL_DIAGNOSIS_REPLY
    assert sources == []


def test_no_retrieval_match_returns_labelled_general_gemini_answer(monkeypatch) -> None:
    monkeypatch.setattr("app.rag.retrieve", lambda _: [])
    monkeypatch.setattr(
        "app.rag._gemini_general_answer", lambda _: "General educational answer."
    )

    answer, sources = answer_question("What is unrelated to this corpus?")

    assert answer == GENERAL_GEMINI_PREFIX + "General educational answer."
    assert sources == []


def test_retrieval_answer_returns_citations(monkeypatch) -> None:
    class Chunk:
        doc = "literature.pdf"
        page = 4
        text = "Relevant literature text."
        distance = 0.2

    monkeypatch.setattr("app.rag.retrieve", lambda _: [Chunk()])
    monkeypatch.setattr("app.rag._gemini_answer", lambda _message, _chunks: "Literature answer.")

    answer, sources = answer_question("What is amyloid?")

    assert answer == "Literature answer."
    assert sources == [{"doc": "literature.pdf", "page": 4}]


def test_unanswered_retrieved_context_uses_labelled_general_gemini_answer(monkeypatch) -> None:
    class Chunk:
        doc = "literature.pdf"
        page = 4
        text = "A different topic."
        distance = 0.2

    monkeypatch.setattr("app.rag.retrieve", lambda _: [Chunk()])
    monkeypatch.setattr("app.rag._gemini_answer", lambda _message, _chunks: NO_MATCH_REPLY)
    monkeypatch.setattr(
        "app.rag._gemini_general_answer", lambda _: "General educational answer."
    )

    answer, sources = answer_question("What does amyloid mean?")

    assert answer == GENERAL_GEMINI_PREFIX + "General educational answer."
    assert sources == []


def test_chat_contract_rejects_prediction_fields() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"message": "What is preclinical Alzheimer's?", "history": [], "AGE": 73},
        )

    assert response.status_code == 422


def test_chat_endpoint_returns_only_answer_and_sources(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.main.answer_question",
        lambda _message: ("Educational answer.", [{"doc": "literature.pdf", "page": 2}]),
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"message": "What is amyloid?", "history": []},
        )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Educational answer.",
        "sources": [{"doc": "literature.pdf", "page": 2}],
    }


def test_chat_ui_payload_is_prediction_free() -> None:
    script = (Path(__file__).parents[1] / "static" / "app.js").read_text(encoding="utf-8")

    assert 'body: JSON.stringify({ message, history })' in script
