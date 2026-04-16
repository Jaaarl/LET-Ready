import sqlite3
import os
import secrets
from datetime import datetime, timezone
from typing import Optional

DB_PATH = os.getenv("USER_DB_PATH", "data/users.db")


def _get_db_path():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH


def init_quiz_tables():
    conn = sqlite3.connect(_get_db_path())
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quiz_sessions (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            subject     TEXT,
            score       INTEGER,
            total       INTEGER,
            created_at  TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wrong_answers (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            question_id TEXT,
            question    TEXT NOT NULL,
            selected    TEXT NOT NULL,
            correct     TEXT NOT NULL,
            answer_text TEXT,
            explanation TEXT,
            subject     TEXT,
            topic       TEXT,
            created_at  TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_wrong_user ON wrong_answers(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session_user ON quiz_sessions(user_id)")
    conn.commit()
    conn.close()


def save_wrong_answer(user_id: str, wrong: dict) -> str:
    conn = sqlite3.connect(_get_db_path())
    wid = secrets.token_hex(12)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO wrong_answers
        (id, user_id, question_id, question, selected, correct, answer_text, explanation, subject, topic, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        wid,
        user_id,
        wrong.get("question_id", ""),
        wrong.get("question", ""),
        wrong.get("selected", ""),
        wrong.get("correct", ""),
        wrong.get("answer_text", ""),
        wrong.get("explanation", ""),
        wrong.get("subject", ""),
        wrong.get("topic", ""),
        now,
    ))
    conn.commit()
    conn.close()
    return wid


def save_wrong_answers_batch(user_id: str, wrong_list: list) -> list:
    ids = []
    for wrong in wrong_list:
        wid = save_wrong_answer(user_id, wrong)
        ids.append(wid)
    return ids


def get_user_wrong_answers(user_id: str, limit: int = 50) -> list:
    conn = sqlite3.connect(_get_db_path())
    rows = conn.execute("""
        SELECT question_id, question, selected, correct, answer_text, explanation, subject, topic
        FROM wrong_answers WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return [
        dict(zip(
            ["question_id", "question", "selected", "correct", "answer_text", "explanation", "subject", "topic"],
            r,
        ))
        for r in rows
    ]


def save_quiz_session(user_id: str, subject: str, score: int, total: int) -> str:
    conn = sqlite3.connect(_get_db_path())
    sid = secrets.token_hex(12)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO quiz_sessions (id, user_id, subject, score, total, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (sid, user_id, subject, score, total, now),
    )
    conn.commit()
    conn.close()
    return sid


def get_quiz_history(user_id: str, limit: int = 20) -> list:
    conn = sqlite3.connect(_get_db_path())
    rows = conn.execute("""
        SELECT subject, score, total, created_at FROM quiz_sessions
        WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return [dict(zip(["subject", "score", "total", "created_at"], r)) for r in rows]
