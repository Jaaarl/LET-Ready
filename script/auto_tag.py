import anthropic
import json
import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────────
INPUT_FILE   = os.getenv("INPUT_FILE",   "let_dataset.json")
OUTPUT_FILE  = os.getenv("OUTPUT_FILE",  "let_dataset_processed.json")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "minimax")
MAX_WORKERS  = int(os.getenv("MAX_WORKERS", "5"))   # parallel threads
RETRY_LIMIT  = int(os.getenv("RETRY_LIMIT", "3"))   # retries on error
RETRY_DELAY  = float(os.getenv("RETRY_DELAY", "2")) # seconds between retries

# ─── Client setup ─────────────────────────────────────────────────────────────
if LLM_PROVIDER == "minimax":
    client = anthropic.Anthropic(
        api_key=os.getenv("MINIMAX_API_KEY"),
        base_url="https://api.minimax.io/anthropic"
    )
    MODEL = "MiniMax-M2.7"
else:
    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    MODEL = "claude-sonnet-4-20250514"

# ─── Thread-safe print & save lock ───────────────────────────────────────────
print_lock = threading.Lock()
save_lock  = threading.Lock()

def safe_print(msg: str):
    with print_lock:
        print(msg)

# ─── Topic definitions ────────────────────────────────────────────────────────
TOPICS = {
    "General Education": [
        "English Grammar",
        "English Vocabulary",
        "Filipino Language",
        "Philippine Literature",
        "Mathematics",
        "Science",
        "Philippine History",
        "Social Studies",
        "Computer Literacy",
        "Values Education",
        "Health Education",
    ],
    "Biology": [
        "Cell Biology",
        "Human Anatomy",
        "Plant Biology",
        "Genetics",
        "Ecology",
        "Microbiology",
        "Physiology",
        "Evolution",
        "Reproduction",
    ],
    "Professional Education": [
        "Child and Adolescent Development",
        "Philosophy of Education",
        "Curriculum Development",
        "Principles of Teaching",
        "Educational Technology",
        "Assessment and Evaluation",
        "Classroom Management",
        "Special Education",
        "Legal Bases of Education",
    ],
}

FALLBACK_TOPICS = ["General Knowledge"]


# ─── Prompt builder ───────────────────────────────────────────────────────────
def build_prompt(question: dict) -> str:
    subject    = question.get("subject", "General Education")
    topics     = TOPICS.get(subject, FALLBACK_TOPICS)
    q_text     = question["question"]
    choices    = question["choices"]
    answer     = question["answer"]
    answer_txt = question["answer_text"]

    choices_block = "\n".join(f"{k}. {v}" for k, v in choices.items())

    return f"""You are a LET (Licensure Examination for Teachers) expert reviewer.

Analyze this exam question carefully and return ONLY valid JSON — no markdown, no explanation, no extra text.

Question: {q_text}

Choices:
{choices_block}

Marked Answer: {answer}. {answer_txt}

Available topics for subject "{subject}":
{json.dumps(topics)}

Return this exact JSON structure:
{{
  "topic": "<one topic from the list above>",
  "explanation": "<2-3 sentence explanation: why the correct answer is right AND briefly why the other choices are wrong. Keep it clear for LET reviewers.>",
  "flag": {{
    "is_flagged": <true or false>,
    "reason": "<if flagged: explain the issue clearly. If not flagged: empty string>"
  }}
}}

Flag the question (is_flagged: true) if ANY of the following issues exist:
- The marked answer appears to be INCORRECT
- The question is ambiguous or has multiple defensible answers
- A choice label is missing or malformed
- The question text is incomplete or garbled
- There is a typo that changes the meaning

Be strict — flag anything suspicious. A flagged question will be reviewed by a human."""


# ─── Extract text from response (handles thinking + text blocks) ──────────────
def extract_text(message) -> str:
    for block in message.content:
        if block.type == "text":
            return block.text
    return ""


# ─── Parse JSON from response ─────────────────────────────────────────────────
def parse_response(message) -> dict:
    raw = extract_text(message).strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


# ─── Process a single question (with retry) ───────────────────────────────────
def process_question(question: dict, index: int, total: int) -> dict:
    qid = question.get("id", f"#{index+1}")

    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": build_prompt(question)
                }]
            )

            parsed = parse_response(message)

            question["topic"]       = parsed.get("topic", "")
            question["explanation"] = parsed.get("explanation", "")
            question["flag"]        = parsed.get("flag", {
                "is_flagged": False,
                "reason": ""
            })

            if question["flag"]["is_flagged"]:
                safe_print(
                    f"  [{index+1}/{total}] {qid} — "
                    f"⚠  FLAGGED: {question['flag']['reason'][:70]}"
                )
            else:
                safe_print(
                    f"  [{index+1}/{total}] {qid} — "
                    f"✅ {question['topic']}"
                )

            return question   # success — exit retry loop

        except json.JSONDecodeError as e:
            safe_print(
                f"  [{index+1}/{total}] {qid} — "
                f"❌ JSON error (attempt {attempt}/{RETRY_LIMIT}): {e}"
            )

        except Exception as e:
            safe_print(
                f"  [{index+1}/{total}] {qid} — "
                f"❌ Error (attempt {attempt}/{RETRY_LIMIT}): {e}"
            )

        if attempt < RETRY_LIMIT:
            time.sleep(RETRY_DELAY * attempt)   # back-off: 2s, 4s, 6s...

    # All retries exhausted — flag it for human review
    safe_print(f"  [{index+1}/{total}] {qid} — ❌ Failed after {RETRY_LIMIT} attempts")
    question["flag"] = {
        "is_flagged": True,
        "reason": f"Failed after {RETRY_LIMIT} attempts — needs manual review"
    }
    return question


# ─── Save helpers ─────────────────────────────────────────────────────────────
def save_all(questions: list):
    with save_lock:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)


def save_flagged(questions: list):
    flagged = [
        q for q in questions
        if q.get("flag", {}).get("is_flagged", False)
    ]
    if not flagged:
        return

    flagged_file = OUTPUT_FILE.replace(".json", "_flagged.json")
    with open(flagged_file, "w", encoding="utf-8") as f:
        json.dump(flagged, f, ensure_ascii=False, indent=2)
    print(f"\n⚠  {len(flagged)} flagged questions → {flagged_file}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  LET Ready — Parallel Question Processor")
    print(f"  Provider : {LLM_PROVIDER.upper()}")
    print(f"  Model    : {MODEL}")
    print(f"  Workers  : {MAX_WORKERS} parallel threads")
    print(f"  Retries  : {RETRY_LIMIT} per question")
    print("=" * 55)

    # Load dataset
    print(f"\nLoading: {INPUT_FILE}")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    total = len(questions)
    print(f"Total questions: {total}")

    # Filter out already processed
    pending_indices = [
        i for i, q in enumerate(questions)
        if not (q.get("topic") and q.get("explanation") and "flag" in q)
    ]
    skipped = total - len(pending_indices)

    if skipped:
        print(f"Already processed: {skipped} — skipping")

    if not pending_indices:
        print("\nAll questions already processed!")
        return

    print(f"To process: {len(pending_indices)}\n")

    start_time = time.time()

    # ── Parallel execution ────────────────────────────────────────────────────
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all pending questions
        future_to_index = {
            executor.submit(
                process_question,
                questions[i],
                i,
                total
            ): i
            for i in pending_indices
        }

        completed = 0
        for future in as_completed(future_to_index):
            idx = future_to_index[future]

            try:
                questions[idx] = future.result()
            except Exception as e:
                safe_print(f"  Unhandled error for index {idx}: {e}")
                questions[idx]["flag"] = {
                    "is_flagged": True,
                    "reason": f"Unhandled error: {e}"
                }

            completed += 1

            # Save every 10 completions to avoid too many writes
            if completed % 10 == 0 or completed == len(pending_indices):
                save_all(questions)
                safe_print(
                    f"\n  💾 Progress saved "
                    f"({completed}/{len(pending_indices)} done)\n"
                )

    # Final save
    save_all(questions)
    save_flagged(questions)

    # ── Summary ───────────────────────────────────────────────────────────────
    elapsed  = time.time() - start_time
    success  = sum(1 for q in questions if not q.get("flag", {}).get("is_flagged") and q.get("topic"))
    flagged  = sum(1 for q in questions if q.get("flag", {}).get("is_flagged"))

    print("\n" + "=" * 55)
    print("  Summary")
    print("=" * 55)
    print(f"  Total      : {total}")
    print(f"  ✅ Success  : {success}")
    print(f"  ⚠  Flagged  : {flagged}")
    print(f"  ⏭  Skipped  : {skipped}")
    print(f"  ⏱  Time     : {elapsed:.1f}s")
    print(f"  ⚡ Speed    : {len(pending_indices)/elapsed:.1f} questions/sec")
    print(f"\n  💾 Output   : {OUTPUT_FILE}")
    print("=" * 55)


if __name__ == "__main__":
    main()