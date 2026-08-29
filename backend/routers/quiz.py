"""
Quiz & Practice Test Generator router.
Produces multiple-choice questions and flashcards from study content.
"""

from fastapi import APIRouter, HTTPException
from models.schemas import QuizRequest, QuizResponse, QuizQuestion, QuizOption, FlashCard
from services.document_store import get_document
from services import llm_client
from typing import List

router = APIRouter()

QUIZ_SYSTEM = """You are an expert educator and exam question designer.
Given study material, generate clear, accurate multiple-choice quiz questions.

Return ONLY a valid JSON array. Each element must have this exact structure:
{
  "question": "...",
  "options": [
    {"label": "A", "text": "..."},
    {"label": "B", "text": "..."},
    {"label": "C", "text": "..."},
    {"label": "D", "text": "..."}
  ],
  "answer": "A",
  "explanation": "Brief reason why this is correct."
}

Rules:
- All 4 options must be plausible but only one correct.
- Questions must cover different parts of the content.
- No repeated questions.
- Return ONLY the JSON array, no markdown fences or extra text.
"""

FLASH_SYSTEM = """You are a study assistant creating concise flashcards.
Given study material, create key concept flashcards.

Return ONLY a valid JSON array. Each element:
{
  "front": "Key term or question",
  "back": "Concise definition or answer (2-3 sentences max)"
}

Return ONLY the JSON array, no markdown fences or extra text.
"""


def _parse_questions(raw: list) -> List[QuizQuestion]:
    questions = []
    for item in raw:
        try:
            options = [
                QuizOption(label=o["label"], text=o["text"])
                for o in item.get("options", [])
            ]
            questions.append(
                QuizQuestion(
                    question=item["question"],
                    options=options,
                    answer=item.get("answer", "A"),
                    explanation=item.get("explanation", ""),
                )
            )
        except (KeyError, TypeError):
            continue
    return questions


def _parse_flashcards(raw: list) -> List[FlashCard]:
    cards = []
    for item in raw:
        try:
            cards.append(FlashCard(front=item["front"], back=item["back"]))
        except (KeyError, TypeError):
            continue
    return cards


@router.post("/generate", response_model=QuizResponse, summary="Generate quiz & flashcards")
async def generate_quiz(req: QuizRequest):
    """
    Generate multiple-choice questions and flashcards from a document or raw text.
    Pass either `doc_id` or `text`. `num_questions` controls question count (1–20).
    """
    if req.doc_id:
        doc = get_document(req.doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        source_text = doc["text"]
    elif req.text:
        source_text = req.text
    else:
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'doc_id'.")

    truncated = source_text[:5000]

    # Generate questions
    q_prompt = (
        f"Generate exactly {req.num_questions} multiple-choice questions "
        f"based on the following content:\n\n{truncated}"
    )
    try:
        raw_questions = llm_client.complete_json(QUIZ_SYSTEM, q_prompt)
        if isinstance(raw_questions, dict):
            raw_questions = [raw_questions]
    except ValueError:
        raw_questions = []

    # Generate flashcards (roughly half the count)
    fc_count = max(1, req.num_questions // 2)
    fc_prompt = f"Create {fc_count} flashcards based on the following content:\n\n{truncated}"
    try:
        raw_flash = llm_client.complete_json(FLASH_SYSTEM, fc_prompt)
        if isinstance(raw_flash, dict):
            raw_flash = [raw_flash]
    except ValueError:
        raw_flash = []

    return QuizResponse(
        questions=_parse_questions(raw_questions),
        flashcards=_parse_flashcards(raw_flash),
    )
