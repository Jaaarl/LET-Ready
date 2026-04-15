from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import quiz, search, chat
import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="LET Ready API",
    description="AI-Powered LET Exam Reviewer",
    version="1.0.0"
)

# ── CORS — allows React frontend to call this API ──────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ChromaDB connection — shared across all routers ────────────────────────
chroma_client = chromadb.PersistentClient(
    path=os.getenv("CHROMA_PATH")
)
collection = chroma_client.get_collection("let_questions")

# Make collection available to routers
app.state.collection = collection

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(quiz.router,   prefix="/quiz",   tags=["Quiz"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(chat.router,   prefix="/chat",   tags=["Chat"])

@app.get("/")
def root():
    return {
        "message": "LET Ready API is running!",
        "questions": collection.count()
    }

@app.get("/health")
def health():
    return {"status": "ok"}