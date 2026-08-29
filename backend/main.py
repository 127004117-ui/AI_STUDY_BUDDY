"""
AI Study Buddy - FastAPI Backend
Production-ready entry point with rate limiting, CORS, and static file serving.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os

from routers import documents, quiz, explain, planner, chatbot

# ── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])

app = FastAPI(
    title="AI Study Buddy",
    description="Personalized Learning Agent — AI-powered study tool",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate limiting middleware ──────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:7000,http://localhost:8000,http://127.0.0.1:7000,http://127.0.0.1:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # fine for public read-only tool; restrict if adding auth
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(explain.router,   prefix="/api/explain",   tags=["ELI10 Explain"])
app.include_router(quiz.router,      prefix="/api/quiz",      tags=["Quiz Generator"])
app.include_router(planner.router,   prefix="/api/planner",   tags=["Revision Planner"])
app.include_router(chatbot.router,   prefix="/api/chat",      tags=["Doubt Chatbot"])

# ── Health (registered before SPA catch-all) ──────────────────────────────────
@app.get("/api/health", tags=["Health"])
async def health_check():
    from services.llm_client import OPENAI_OK, GEMINI_OK
    mode = "openai" if OPENAI_OK else ("gemini" if GEMINI_OK else "demo")
    return {
        "status": "ok",
        "message": "AI Study Buddy is running",
        "ai_mode": mode,
        "version": "1.0.0",
    }

# ── Serve frontend static files ───────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.isdir(FRONTEND_DIR):
    static_dir = os.path.join(FRONTEND_DIR, "static")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not found"}, status_code=404)
        target = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(target):
            return FileResponse(target)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
