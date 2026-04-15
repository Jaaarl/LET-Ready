from fastapi import APIRouter, Request
from pydantic import BaseModel
import anthropic
import os

router = APIRouter()

# ── MiniMax client ─────────────────────────────────────────────────────────
llm_client = anthropic.Anthropic(
    api_key=os.getenv("MINIMAX_API_KEY"),
    base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic")
)

class ChatRequest(BaseModel):
    message: str
    subject: str = None


@router.post("/")
def chat(req: ChatRequest, request: Request):
    """RAG-powered chat — retrieves relevant questions then answers."""
    collection = request.app.state.collection

    # Step 1: Retrieve relevant questions from ChromaDB
    where = {"subject": req.subject} if req.subject else None

    results = collection.query(
        query_texts=[req.message],
        n_results=5,
        where=where
    )

    # Step 2: Build context from retrieved questions
    context_parts = []
    for meta in results["metadatas"][0]:
        context_parts.append(f"""
Question: {meta['question']}
A. {meta['choice_a']}
B. {meta['choice_b']}
C. {meta['choice_c']}
D. {meta['choice_d']}
Correct Answer: {meta['answer']}. {meta['answer_text']}
Explanation: {meta['explanation']}
        """.strip())

    context = "\n\n---\n\n".join(context_parts)

    # Step 3: Generate answer with MiniMax
    system_prompt = """You are an expert LET (Licensure Examination for Teachers) reviewer assistant.
Use the provided exam questions and explanations to help the user study.
Always cite which question you are referencing.
Be encouraging and clear in your explanations."""

    user_prompt = f"""Based on these LET exam questions:

{context}

User question: {req.message}

Please provide a helpful study response."""

    response = llm_client.messages.create(
        model="MiniMax-M2.7",
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    # Extract text from response
    answer = ""
    for block in response.content:
        if block.type == "text":
            answer = block.text
            break

    return {
        "answer":   answer,
        "sources":  len(results["metadatas"][0]),
        "context":  context_parts
    }