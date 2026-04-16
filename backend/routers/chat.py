from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
import anthropic
import os
from auth.dependencies import optional_user
from models.quiz import get_user_wrong_answers

router = APIRouter()

# ── MiniMax client ─────────────────────────────────────────────────────────
llm_client = anthropic.Anthropic(
    api_key=os.getenv("MINIMAX_API_KEY"),
    base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic")
)

class ChatRequest(BaseModel):
    message: str
    subject: str | None = None
    wrong_answers: list = []


@router.post("/")
def chat(req: ChatRequest, request: Request, user: dict = Depends(optional_user)):
    """AI tutor — focuses on user's wrong answers, supplemented by RAG."""
    collection = request.app.state.collection

    # Step 1: Load personal wrong answers from DB for logged-in users
    personal_wrong = get_user_wrong_answers(user["id"]) if user else []

    # Step 2: Merge — session wrong answers first (recent), then DB history
    all_wrong = req.wrong_answers + personal_wrong

    # Step 3: Build context from wrong answers (priority)
    context_parts = []
    seen_questions = set()
    for wrong in all_wrong:
        q_key = wrong.get("question", "")[:50]  # dedupe by question prefix
        if q_key in seen_questions:
            continue
        seen_questions.add(q_key)
        topic = wrong.get("topic", "Unknown topic")
        subject = wrong.get("subject", "Unknown subject")
        context_parts.append(f"""
Wrong Answer Discussion:
Subject: {subject}
Topic: {topic}
Question: {wrong.get('question', 'N/A')}
Your Answer: {wrong.get('selected', 'N/A')}
Correct Answer: {wrong.get('correct', 'N/A')}. {wrong.get('answer_text', '')}
Explanation: {wrong.get('explanation', 'No explanation available.')}
        """.strip())

    # Step 4: If user asks a new question, supplement with RAG
    if req.message.strip():
        where = {"subject": req.subject} if req.subject else None
        rag_results = collection.query(
            query_texts=[req.message],
            n_results=3,
            where=where
        )
        for meta in rag_results["metadatas"][0]:
            context_parts.append(f"""
RAG Reference:
Question: {meta['question']}
A. {meta['choice_a']}
B. {meta['choice_b']}
C. {meta['choice_c']}
D. {meta['choice_d']}
Correct Answer: {meta['answer']}. {meta['answer_text']}
Explanation: {meta['explanation']}
            """.strip())

    context = "\n\n---\n\n".join(context_parts)

    # Step 5: Generate answer with MiniMax
    has_wrong = len(all_wrong) > 0
    system_prompt = f"""You are a friendly and warm LET exam tutor, like a supportive older sibling helping a student study.
{"You are currently helping {user['name']} understand questions they got wrong." if has_wrong and user else ""}
{"You are helping a student understand questions they got wrong." if has_wrong and not user else ""}

Guidelines:
- Explain concepts in a conversational, natural tone — not like a textbook or lecture
- Use simple words and short sentences. Avoid sounding robotic or overly academic
- Break down tricky concepts step-by-step with everyday examples
- Be encouraging — celebrate small wins, don't make the student feel dumb for mistakes
- Use bullet points (•) and numbered lists instead of markdown tables — tables break in chat
- When explaining wrong answers, focus on the "aha moment" — why the right answer makes sense
- Keep explanations focused and digestible — no walls of text
{"Focus on explaining the concepts behind the student's mistakes in a friendly, easy-to-understand way." if has_wrong else ""}"""

    user_prompt = f"""Based on these LET exam questions and discussions:

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
        "sources":  len(all_wrong) + (3 if req.message.strip() else 0),
        "context":  context_parts
    }
