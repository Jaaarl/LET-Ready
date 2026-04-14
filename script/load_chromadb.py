import chromadb
import json
import os
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE  = os.getenv("OUTPUT_FILE")
CHROMA_PATH = os.getenv("CHROMA_PATH")

# ── Setup ChromaDB ─────────────────────────────────────────────────────────
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(
    name="let_questions",
    metadata={"hnsw:space": "cosine"}
)

# ── Load dataset ───────────────────────────────────────────────────────────
print(f"Loading: {INPUT_FILE}")
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    questions = json.load(f)

print(f"Total questions: {len(questions)}")

# ── Skip flagged questions ─────────────────────────────────────────────────
clean = [
    q for q in questions
    if not q.get("flag", {}).get("is_flagged", False)
]
skipped = len(questions) - len(clean)
print(f"Skipping {skipped} flagged questions")
print(f"Loading {len(clean)} clean questions into ChromaDB\n")

# ── Prepare data ───────────────────────────────────────────────────────────
ids        = []
documents  = []
metadatas  = []

for q in clean:
    ids.append(q["id"])

    # This is what gets embedded — rich text for better retrieval
    doc = f"""
Subject: {q.get('subject', '')}
Topic: {q.get('topic', '')}
Question: {q.get('question', '')}
A. {q['choices'].get('A', '')}
B. {q['choices'].get('B', '')}
C. {q['choices'].get('C', '')}
D. {q['choices'].get('D', '')}
Correct Answer: {q.get('answer', '')}. {q.get('answer_text', '')}
Explanation: {q.get('explanation', '')}
    """.strip()
    documents.append(doc)

    metadatas.append({
        "part":        q.get("part", ""),
        "subject":     q.get("subject", ""),
        "topic":       q.get("topic", "") or "",
        "question":    q.get("question", ""),
        "choice_a":    q["choices"].get("A", ""),
        "choice_b":    q["choices"].get("B", ""),
        "choice_c":    q["choices"].get("C", ""),
        "choice_d":    q["choices"].get("D", ""),
        "answer":      q.get("answer", ""),
        "answer_text": q.get("answer_text", ""),
        "explanation": q.get("explanation", ""),
        "source":      q.get("source", ""),
    })

# ── Load in batches of 50 ──────────────────────────────────────────────────
BATCH_SIZE = 50
total = len(clean)

for i in range(0, total, BATCH_SIZE):
    batch_ids  = ids[i:i+BATCH_SIZE]
    batch_docs = documents[i:i+BATCH_SIZE]
    batch_meta = metadatas[i:i+BATCH_SIZE]

    collection.add(
        ids=batch_ids,
        documents=batch_docs,
        metadatas=batch_meta
    )
    print(f"  Loaded {min(i+BATCH_SIZE, total)}/{total}")

print(f"\n✅ Done! {collection.count()} questions in ChromaDB")
print(f"📁 Database saved at: {CHROMA_PATH}")