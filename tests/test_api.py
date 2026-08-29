"""
Tests for core API endpoints.
Run with: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
import sys, os

# Ensure backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app

client = TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Documents ─────────────────────────────────────────────────────────────────

def test_list_documents_empty():
    r = client.get("/api/documents/list")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_upload_txt_document():
    content = b"Photosynthesis is the process by which green plants convert sunlight into food."
    r = client.post(
        "/api/documents/upload",
        files={"file": ("test_notes.txt", content, "text/plain")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "doc_id" in data
    assert data["filename"] == "test_notes.txt"
    assert data["word_count"] > 0


def test_upload_unsupported_format():
    r = client.post(
        "/api/documents/upload",
        files={"file": ("notes.docx", b"fake", "application/octet-stream")},
    )
    assert r.status_code == 415


# ── ELI10 ─────────────────────────────────────────────────────────────────────

def test_eli10_with_text():
    r = client.post(
        "/api/explain/eli10",
        json={"text": "Quantum entanglement is a physical phenomenon that occurs when pairs of particles interact."},
    )
    assert r.status_code == 200
    data = r.json()
    assert "simplified" in data
    assert len(data["simplified"]) > 10


def test_eli10_missing_input():
    r = client.post("/api/explain/eli10", json={})
    assert r.status_code in (400, 422)


# ── Quiz ──────────────────────────────────────────────────────────────────────

def test_quiz_with_text():
    r = client.post(
        "/api/quiz/generate",
        json={
            "text": "The mitochondria is the powerhouse of the cell. It produces ATP through cellular respiration.",
            "num_questions": 1,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "questions" in data
    assert "flashcards" in data


# ── Planner ───────────────────────────────────────────────────────────────────

def test_planner_future_date():
    from datetime import date, timedelta
    future = (date.today() + timedelta(days=14)).isoformat()
    r = client.post(
        "/api/planner/schedule",
        json={"exam_date": future, "topics": ["Math", "Physics", "Chemistry"], "daily_hours": 2},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total_days"] == 14
    assert len(data["daily_plan"]) == 14


def test_planner_past_date():
    r = client.post(
        "/api/planner/schedule",
        json={"exam_date": "2020-01-01", "topics": ["Math"], "daily_hours": 2},
    )
    assert r.status_code == 400


# ── Chatbot ───────────────────────────────────────────────────────────────────

def test_chat_no_doc():
    r = client.post(
        "/api/chat/ask",
        json={"question": "What is gravity?", "history": []},
    )
    assert r.status_code == 200
    assert "answer" in r.json()


def test_chat_missing_doc():
    r = client.post(
        "/api/chat/ask",
        json={"question": "Explain this.", "doc_id": "nonexistent"},
    )
    assert r.status_code == 404
