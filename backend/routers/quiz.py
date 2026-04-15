from fastapi import APIRouter, Request
import random

router = APIRouter()

@router.get("/random")
def get_random_question(request: Request, subject: str = None):
    """Get a random question, optionally filtered by subject."""
    collection = request.app.state.collection

    where = {"subject": subject} if subject else None

    # Get more than needed then pick random
    results = collection.query(
        query_texts=["exam question"],
        n_results=50,
        where=where
    )

    if not results["metadatas"][0]:
        return {"error": "No questions found"}

    # Pick one randomly
    idx  = random.randint(0, len(results["metadatas"][0]) - 1)
    meta = results["metadatas"][0][idx]

    return format_question(meta)


@router.get("/by-topic")
def get_question_by_topic(request: Request, topic: str, n: int = 5):
    """Get questions filtered by topic."""
    collection = request.app.state.collection

    results = collection.query(
        query_texts=[topic],
        n_results=n,
        where={"topic": topic}
    )

    questions = [
        format_question(meta)
        for meta in results["metadatas"][0]
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


def format_question(meta: dict) -> dict:
    return {
        "question":  meta["question"],
        "subject":   meta["subject"],
        "topic":     meta["topic"],
        "choices": {
            "A": meta["choice_a"],
            "B": meta["choice_b"],
            "C": meta["choice_c"],
            "D": meta["choice_d"],
        }
    }