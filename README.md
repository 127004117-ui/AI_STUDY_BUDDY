# 🎓 AI Study Buddy — Personalized Learning Agent

A full-stack AI application that helps students study smarter. Upload your notes, get simplified explanations, generate quizzes, build a revision plan, and ask your AI tutor anything — all in one place.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📂 **Document Upload** | Upload PDF, TXT, or Markdown study notes |
| ✨ **ELI10 Explain** | Simplifies complex concepts for beginners |
| 🎯 **Quiz Generator** | Auto-generates MCQ questions + flashcards with answer keys |
| 📅 **Revision Planner** | Creates a day-by-day revision schedule from your exam date |
| 💬 **Study Chatbot** | Context-aware Q&A over your uploaded documents |

---

## 🗂 Project Structure

```
ai-study-buddy/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # API key template
│   ├── routers/
│   │   ├── documents.py         # Upload / list / delete documents
│   │   ├── explain.py           # ELI10 simplification endpoint
│   │   ├── quiz.py              # Quiz + flashcard generation
│   │   ├── planner.py           # Smart revision schedule
│   │   └── chatbot.py           # Doubt-solving Q&A chat
│   ├── services/
│   │   ├── document_store.py    # In-memory doc store + text extraction
│   │   └── llm_client.py        # OpenAI / Gemini / Demo LLM abstraction
│   └── models/
│       └── schemas.py           # Pydantic request/response models
├── frontend/
│   ├── index.html               # Single-page app shell
│   └── static/
│       ├── style.css            # Responsive dark-mode UI
│       └── app.js               # All frontend logic (vanilla JS)
├── tests/
│   └── test_api.py              # Pytest suite for all endpoints
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & enter the project

```bash
cd ai-study-buddy
```

### 2. Set up Python environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys (optional)

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY or GEMINI_API_KEY
```

> **No keys?** The app runs in **Demo Mode** — all endpoints return smart placeholder responses. Perfect for testing the UI.

### 5. Start the backend

```bash
uvicorn main:app --reload --port 8000
```

### 6. Open the frontend

**Option A — Served by FastAPI (recommended):**
Visit `http://localhost:8000`

**Option B — Open directly in browser:**
Open `frontend/index.html` directly. The frontend auto-detects `localhost:8000` as the API base.

---

## 🔑 API Keys

| Provider | Environment Variable | Model Used |
|---|---|---|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o-mini` |
| Google Gemini | `GEMINI_API_KEY` | `gemini-1.5-flash` |
| Demo Mode | *(none required)* | Built-in mock responses |

The [`llm_client.py`](backend/services/llm_client.py) automatically selects the available provider in priority order: OpenAI → Gemini → Demo.

---

## 📡 API Reference

All endpoints are also available at `http://localhost:8000/docs` (Swagger UI) and `/redoc`.

### Documents
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/documents/upload` | Upload a file (multipart/form-data) |
| `GET` | `/api/documents/list` | List all uploaded documents |
| `DELETE` | `/api/documents/{doc_id}` | Delete a document |

### ELI10 Explain
| Method | Endpoint | Body |
|---|---|---|
| `POST` | `/api/explain/eli10` | `{ "text": "..." }` or `{ "doc_id": "abc123" }` |

### Quiz Generator
| Method | Endpoint | Body |
|---|---|---|
| `POST` | `/api/quiz/generate` | `{ "doc_id": "abc123", "num_questions": 5 }` |

### Revision Planner
| Method | Endpoint | Body |
|---|---|---|
| `POST` | `/api/planner/schedule` | `{ "exam_date": "2025-08-01", "topics": ["Math", "Physics"], "daily_hours": 2 }` |

### Chatbot
| Method | Endpoint | Body |
|---|---|---|
| `POST` | `/api/chat/ask` | `{ "doc_id": "abc123", "question": "What is X?", "history": [...] }` |

---

## 🧪 Running Tests

```bash
cd ai-study-buddy
pip install pytest httpx
pytest tests/ -v
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| LLM | OpenAI GPT-4o-mini / Google Gemini 1.5 Flash |
| PDF Parsing | pdfplumber |
| Frontend | Vanilla HTML + CSS + JavaScript (no build step) |
| Data Models | Pydantic v2 |
| Testing | pytest + httpx |

---

## 📝 Notes

- **Document storage is in-memory** — documents reset when the server restarts. For persistence, swap [`document_store.py`](backend/services/document_store.py) with a database (SQLite/PostgreSQL).
- **Token limits** — large documents are automatically truncated to the first 4,000–5,000 characters for LLM calls to stay within context limits.
- **CORS** is open (`*`) for development. Restrict to your domain in production.

---

## 📄 License

MIT — free to use and modify.
