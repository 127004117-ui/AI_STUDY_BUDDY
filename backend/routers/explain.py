"""
ELI10 (Explain Like I'm 10) router.
Simplifies complex study text into beginner-friendly language.
"""

from fastapi import APIRouter, HTTPException
from models.schemas import ExplainRequest, ExplainResponse
from services.document_store import get_document
from services import llm_client

router = APIRouter()

ELI10_SYSTEM = """You are a friendly tutor who explains things as simply as possible.
Your goal is to take complex academic or technical text and rewrite it so that
a 10-year-old child can understand it perfectly.

Rules:
- Use short, simple sentences.
- Replace jargon with everyday words or relatable analogies.
- Keep all key facts intact — just make them understandable.
- Use bullet points where helpful.
- Start with a one-sentence summary of what the topic is about.
"""


@router.post("/eli10", response_model=ExplainResponse, summary="Simplify text (ELI10 mode)")
async def explain_eli10(req: ExplainRequest):
    """
    Simplify the provided text or a stored document into plain, easy-to-understand language.
    Pass either `text` directly or a `doc_id` referencing an uploaded document.
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

    # Truncate to avoid excessive token usage
    truncated = source_text[:4000]

    user_prompt = f"Please explain the following text in ELI10 style:\n\n{truncated}"
    simplified = llm_client.complete(ELI10_SYSTEM, user_prompt, temperature=0.6)

    return ExplainResponse(
        original_length=len(source_text.split()),
        simplified=simplified,
    )
