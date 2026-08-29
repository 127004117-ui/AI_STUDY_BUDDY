"""
Doubt-Solving Chatbot router.
Context-aware QA over uploaded study materials with conversation history.
"""

from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from services.document_store import get_document
from services import llm_client

router = APIRouter()

BASE_SYSTEM = """You are an intelligent, patient, and encouraging AI Study Buddy.
Your job is to help students understand their study material by answering doubts clearly.

Guidelines:
- Always base answers on the provided document context when available.
- If the answer is not in the context, say so honestly but still try to help with general knowledge.
- Use examples and analogies to make concepts clear.
- Be concise: 2–5 sentences unless a longer explanation is genuinely needed.
- Encourage the student when they show understanding.
- Never make up facts. If uncertain, say "I'm not sure — please verify this."
"""

def _build_history_text(history: list) -> str:
    lines = []
    for msg in history[-6:]:  # last 6 turns to stay within token limits
        prefix = "Student" if msg.role == "user" else "Tutor"
        lines.append(f"{prefix}: {msg.content}")
    return "\n".join(lines)


@router.post("/ask", response_model=ChatResponse, summary="Ask a study question")
async def ask_question(req: ChatRequest):
    """
    Ask a question about uploaded study material.
    - Optionally reference a document via `doc_id` for context-aware answers.
    - Pass `history` to maintain a multi-turn conversation.
    """
    context_section = ""
    sources = []

    if req.doc_id:
        doc = get_document(req.doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        # Use the first 4000 chars of the document as context
        context_section = f"\n\n=== STUDY DOCUMENT: {doc['filename']} ===\n{doc['text'][:4000]}\n==="
        sources = [doc["filename"]]

    history_text = _build_history_text(req.history)
    conversation_block = f"\n\nConversation so far:\n{history_text}" if history_text else ""

    user_prompt = (
        f"{context_section}"
        f"{conversation_block}"
        f"\n\nStudent's question: {req.question}"
        f"\n\nPlease answer the student's question clearly and helpfully."
    )

    answer = llm_client.complete(BASE_SYSTEM, user_prompt, temperature=0.5)

    return ChatResponse(answer=answer, sources=sources)
