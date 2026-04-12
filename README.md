# 🎓 LET Ready — AI-Powered LET Exam Reviewer

An adaptive LET (Licensure Examination for Teachers) reviewer
powered by RAG (Retrieval-Augmented Generation), built with
MiniMax LLM, ChromaDB, and FastAPI.

## 🧠 How It Works

1. LET questions are extracted from PDFs and structured as JSON
2. Questions are embedded using Jina AI and stored in ChromaDB
3. When a user asks a question, RAG retrieves relevant content
4. MiniMax LLM generates an answer with explanation and citations

## ✨ Features

- 📚 500+ LET questions across all subjects
- 🎯 Adaptive quiz — focuses on your weak areas
- 🧠 AI-generated explanations per question
- 📊 Personal performance dashboard
- ⏱️ Exam simulation mode (timed)
- 📅 Study plan generator
- 🔖 Bookmarks and personal notes

## 🛠️ Tech Stack

| Layer     | Technology       |
| --------- | ---------------- |
| LLM       | MiniMax          |
| Embedding | Jina AI          |
| Vector DB | ChromaDB         |
| Backend   | FastAPI          |
| Frontend  | React + Tailwind |
