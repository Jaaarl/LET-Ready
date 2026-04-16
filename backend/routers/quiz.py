from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import random
from auth.dependencies import optional_user
from models.quiz import save_quiz_session, save_wrong_answers_batch

router = APIRouter()

@router.get("/random")
def get_random_question(request: Request, subject: str = None):
    collection = request.app.state.collection

    where = {"subject": subject} if subject else None

    results = collection.query(
        query_texts=["exam question"],
        n_results=50,
        where=where
    )

    if not results["metadatas"][0]:
        return {"error": "No questions found"}

    import random
    idx  = random.randint(0, len(results["metadatas"][0]) - 1)
    meta = results["metadatas"][0][idx]
    # ✅ Pass the actual ChromaDB document ID
    doc_id = results["ids"][0][idx]

    return format_question(meta, doc_id)


@router.get("/by-topic")
def get_question_by_topic(request: Request, topic: str, n: int = 5):
    collection = request.app.state.collection

    results = collection.query(
        query_texts=[topic],
        n_results=n,
        where={"topic": topic}
    )

    questions = [
        format_question(meta, doc_id)
        for meta, doc_id in zip(
            results["metadatas"][0],
            results["ids"][0]
        )
    ]
    return {"questions": questions, "total": len(questions)}



@router.post("/check-answer")
def check_answer(request: Request, question_id: str, selected: str):
    """Check if the selected answer is correct."""
    collection = request.app.state.collection

    results = collection.get(ids=[question_id])

    if not results["metadatas"]:
        return {"error": "Question not found"}

    meta       = results["metadatas"][0]
    is_correct = selected.upper() == meta["answer"].upper()

    return {
        "is_correct":   is_correct,
        "correct":      meta["answer"],
        "answer_text":  meta["answer_text"],
        "explanation":  meta["explanation"],
    }


def format_question(meta: dict, doc_id: str = None) -> dict:
    return {
        "id":        doc_id or "",
        "question":  meta["question"],
        "subject":   meta["subject"],
        "topic":     meta["topic"],
        "answer":    meta["answer"],
        "choices": {
            "A": meta["choice_a"],
            "B": meta["choice_b"],
            "C": meta["choice_c"],
            "D": meta["choice_d"],
        }
    }


class SaveSessionRequest(BaseModel):
    subject: str
    score: int
    total: int
    wrong_answers: list


@router.post("/save-session")
def post_save_session(
    body: SaveSessionRequest,
    user: dict = None,
):
    """Save quiz results — only for logged-in users."""
    if not user:
        raise HTTPException(status_code=401, detail="Login required to save progress")
    save_quiz_session(user["id"], body.subject, body.score, body.total)
    if body.wrong_answers:
        save_wrong_answers_batch(user["id"], body.wrong_answers)
    return {"saved": True}
