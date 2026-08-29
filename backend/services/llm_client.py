"""
LLM Client abstraction.

Priority order (falls back automatically):
  1. OpenAI (GPT-4o-mini)   — set OPENAI_API_KEY in .env
  2. Google Gemini           — set GEMINI_API_KEY in .env
  3. Offline demo mode       — no keys required (smart contextual responses)
"""

import os
import json
import re

# ── Load .env if present ──────────────────────────────────────────────────────
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.isfile(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# ── Provider detection ────────────────────────────────────────────────────────
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

OPENAI_OK = False
GEMINI_OK = False

if OPENAI_KEY and not OPENAI_KEY.startswith("sk-..."):
    try:
        import openai as _openai_mod
        OPENAI_OK = True
    except ImportError:
        pass

if GEMINI_KEY and not GEMINI_KEY.startswith("AIza..."):
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        GEMINI_OK = True
    except ImportError:
        pass


# ── OpenAI ────────────────────────────────────────────────────────────────────
def _call_openai(system: str, user: str, temperature: float = 0.7) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_KEY)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()


# ── Gemini ────────────────────────────────────────────────────────────────────
def _call_gemini(system: str, user: str, temperature: float = 0.7) -> str:
    import google.generativeai as genai
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"{system}\n\n{user}"
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(temperature=temperature),
    )
    return response.text.strip()


# ── Demo / Offline mode ───────────────────────────────────────────────────────
def _demo_eli10(context: str) -> str:
    # Extract first sentence or two for a contextual mock
    sentences = [s.strip() for s in re.split(r'[.!?]', context) if len(s.strip()) > 20]
    topic = sentences[0][:80] if sentences else "this topic"
    return (
        f"🧒 Here's a simple explanation:\n\n"
        f"Imagine you're learning about: \"{topic}...\"\n\n"
        f"Think of it like this — it's just like how you learn to ride a bike. "
        f"First you understand the basics, then you practice, and soon it becomes easy!\n\n"
        f"The main idea here is about understanding key concepts step by step. "
        f"Every big idea is just made up of smaller, simpler ideas put together.\n\n"
        f"💡 To get real AI-powered explanations, add your OpenAI API key to the .env file."
    )


def _demo_quiz(context: str, num: int = 5) -> list:
    # Extract some words from context to make slightly contextual questions
    words = [w for w in re.findall(r'[A-Z][a-z]{3,}', context) if len(w) > 4]
    unique_words = list(dict.fromkeys(words))[:10]
    topic_a = unique_words[0] if len(unique_words) > 0 else "Concept A"
    topic_b = unique_words[1] if len(unique_words) > 1 else "Concept B"
    topic_c = unique_words[2] if len(unique_words) > 2 else "Concept C"

    questions = [
        {
            "question": f"What is the primary purpose of {topic_a} as described in the material?",
            "options": [
                {"label": "A", "text": f"To define and explain {topic_a}"},
                {"label": "B", "text": "To provide historical background only"},
                {"label": "C", "text": "To list unrelated facts"},
                {"label": "D", "text": "None of the above"},
            ],
            "answer": "A",
            "explanation": f"{topic_a} is introduced to explain a key concept in the material.",
        },
        {
            "question": f"Which of the following best describes {topic_b}?",
            "options": [
                {"label": "A", "text": "An unimportant detail"},
                {"label": "B", "text": f"A core concept related to {topic_b}"},
                {"label": "C", "text": "A contradicting idea"},
                {"label": "D", "text": "A historical figure"},
            ],
            "answer": "B",
            "explanation": f"{topic_b} is a core concept covered in the study material.",
        },
        {
            "question": "What is the best study strategy for understanding this material?",
            "options": [
                {"label": "A", "text": "Reading once quickly"},
                {"label": "B", "text": "Skipping difficult parts"},
                {"label": "C", "text": "Active recall and spaced repetition"},
                {"label": "D", "text": "Memorizing without understanding"},
            ],
            "answer": "C",
            "explanation": "Active recall with spaced repetition is proven to be the most effective study method.",
        },
        {
            "question": f"How does {topic_c} relate to the broader topic in the document?",
            "options": [
                {"label": "A", "text": f"{topic_c} is the central theme"},
                {"label": "B", "text": f"{topic_c} contradicts the main idea"},
                {"label": "C", "text": f"{topic_c} is not mentioned"},
                {"label": "D", "text": "It is only a minor footnote"},
            ],
            "answer": "A",
            "explanation": f"{topic_c} appears as a significant term, likely central to the topic.",
        },
        {
            "question": "Which approach helps retain information from study notes the longest?",
            "options": [
                {"label": "A", "text": "Passive re-reading"},
                {"label": "B", "text": "Highlighting everything"},
                {"label": "C", "text": "Teaching the concept to someone else"},
                {"label": "D", "text": "Studying only the night before"},
            ],
            "answer": "C",
            "explanation": "The Feynman technique — explaining concepts in simple terms — is one of the best retention methods.",
        },
    ]
    return questions[:max(1, min(num, 5))]


def _demo_flashcards(context: str, num: int = 3) -> list:
    words = [w for w in re.findall(r'[A-Z][a-z]{3,}', context) if len(w) > 4]
    unique_words = list(dict.fromkeys(words))[:6]

    cards = []
    for i, word in enumerate(unique_words[:num]):
        cards.append({
            "front": f"What is {word}?",
            "back": f"{word} is a key concept in this study material. Review the document for its full definition and context.",
        })
    if not cards:
        cards = [
            {"front": "What is active recall?", "back": "A study technique where you actively stimulate memory during learning rather than passively re-reading."},
            {"front": "What is spaced repetition?", "back": "A learning method where you review material at increasing intervals to strengthen long-term memory."},
            {"front": "What is the Feynman technique?", "back": "Explaining a concept in simple language as if teaching a child, which reveals gaps in understanding."},
        ]
    return cards[:num]


def _demo_chat(question: str, context: str) -> str:
    q = question.lower()
    if any(w in q for w in ["what is", "define", "explain", "meaning"]):
        return (
            f"Based on the study material, I can see this topic relates to key concepts in your document. "
            f"In simple terms: the subject you're asking about is an important idea that connects to the broader theme of your notes.\n\n"
            f"💡 For precise AI-powered answers based on your exact document, add your OpenAI API key to the `.env` file and restart the server."
        )
    if any(w in q for w in ["summarize", "summary", "overview", "brief"]):
        words = context.split()[:60]
        preview = " ".join(words) + "..."
        return (
            f"Here's a brief overview based on the beginning of your document:\n\n"
            f"\"{preview}\"\n\n"
            f"The material covers several important concepts. I recommend going through each section carefully and using the Quiz Generator to test your understanding!"
        )
    if any(w in q for w in ["how", "why", "when", "where", "who"]):
        return (
            f"Great question! Based on your study material, this is an important concept to understand. "
            f"I'd recommend focusing on the key definitions and examples in your notes.\n\n"
            f"Try using the **ELI10 tab** to get a simplified explanation of any complex section, "
            f"or the **Quiz tab** to test yourself on this topic!"
        )
    return (
        f"I've reviewed your study material and found relevant information. "
        f"Your question about \"{question[:60]}\" touches on key concepts in the document.\n\n"
        f"📚 Tip: Upload your notes and use the Quiz Generator to create practice questions on this exact topic!\n\n"
        f"💡 For full AI-powered answers, add your `OPENAI_API_KEY` to the `.env` file."
    )


# ── Public interface ──────────────────────────────────────────────────────────

def complete(system: str, user: str, temperature: float = 0.7) -> str:
    """Send a chat completion — falls back to smart demo if no API key."""
    if OPENAI_OK:
        try:
            return _call_openai(system, user, temperature)
        except Exception as e:
            print(f"[OpenAI error] {e}")
    if GEMINI_OK:
        try:
            return _call_gemini(system, user, temperature)
        except Exception as e:
            print(f"[Gemini error] {e}")

    # Demo mode — pick the right mock based on context
    context = user[:1000]
    if "ELI10" in system or "simple" in system.lower() or "10-year" in system.lower():
        return _demo_eli10(context)
    if "quiz" in system.lower() or "multiple-choice" in system.lower():
        num = 5
        m = re.search(r'exactly (\d+)', user)
        if m:
            num = int(m.group(1))
        return json.dumps(_demo_quiz(context, num))
    if "flashcard" in system.lower():
        num = 3
        m = re.search(r'Create (\d+)', user)
        if m:
            num = int(m.group(1))
        return json.dumps(_demo_flashcards(context, num))
    return _demo_chat(user[:200], context)


def complete_json(system: str, user: str) -> list | dict:
    """Like complete() but parses and returns JSON."""
    raw = complete(system, user, temperature=0.3)
    # Strip markdown fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"(\[.*\]|\{.*\})", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        # Last resort: return a safe empty list so UI doesn't crash
        print(f"[LLM] Could not parse JSON response: {raw[:200]}")
        return []
