from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/")
def search_questions(
    request: Request,
    q: str,
    subject: str = None,
    topic: str   = None,
    n: int       = 5
):
    """Search questions by meaning using RAG."""
    collection = request.app.state.collection

    # Build filter
    where = {}
    if subject:
        where["subject"] = subject
    if topic:
        where["topic"] = topic

    results = collection.query(
        query_texts=[q],
        n_results=n,
        where=where if where else None
    )

    questions = []
    for i, meta in enumerate(results["metadatas"][0]):
        questions.append({
            "rank":      i + 1,
            "question":  meta["question"],
            "subject":   meta["subject"],
            "topic":     meta["topic"],
            "answer":    meta["answer"],
            "answer_text": meta["answer_text"],
            "choices": {
                "A": meta["choice_a"],
                "B": meta["choice_b"],
                "C": meta["choice_c"],
                "D": meta["choice_d"],
            }
        })

    return {
        "query":     q,
        "results":   questions,
        "total":     len(questions)
    }