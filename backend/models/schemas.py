"""
Pydantic schemas shared across routers.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


# ── Document ──────────────────────────────────────────────────────────────────

class DocumentMeta(BaseModel):
    doc_id: str
    filename: str
    content_preview: str
    word_count: int


# ── ELI10 ─────────────────────────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to simplify")
    doc_id: Optional[str] = Field(None, description="Use stored document instead")


class ExplainResponse(BaseModel):
    original_length: int
    simplified: str


# ── Quiz ──────────────────────────────────────────────────────────────────────

class QuizOption(BaseModel):
    label: str   # A, B, C, D
    text: str


class QuizQuestion(BaseModel):
    question: str
    options: List[QuizOption]
    answer: str          # label of correct option
    explanation: str


class FlashCard(BaseModel):
    front: str
    back: str


class QuizRequest(BaseModel):
    doc_id: Optional[str] = None
    text: Optional[str] = None
    num_questions: int = Field(5, ge=1, le=20)


class QuizResponse(BaseModel):
    questions: List[QuizQuestion]
    flashcards: List[FlashCard]


# ── Revision Planner ──────────────────────────────────────────────────────────

class PlannerRequest(BaseModel):
    exam_date: date
    topics: List[str] = Field(..., min_length=1)
    daily_hours: float = Field(2.0, ge=0.5, le=12.0)


class DayPlan(BaseModel):
    date: str
    topics: List[str]
    hours: float


class PlannerResponse(BaseModel):
    total_days: int
    daily_plan: List[DayPlan]
    message: str


# ── Chatbot ───────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    doc_id: Optional[str] = None
    history: List[ChatMessage] = []
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
