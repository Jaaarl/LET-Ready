import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

DB_PATH = os.getenv("USER_DB_PATH", "data/users.db")


def _get_db_path():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH


def init_db():
    path = _get_db_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id           TEXT PRIMARY KEY,
            email        TEXT UNIQUE NOT NULL,
            name         TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at   TEXT NOT NULL,
            updated_at   TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def create_user(email: str, name: str, password: str) -> dict:
    conn = sqlite3.connect(_get_db_path())
    uid = secrets.token_hex(16)
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute(
            "INSERT INTO users (id, email, name, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, email, name, pw_hash, now, now),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Email already registered")
    conn.close()
    return {"id": uid, "email": email, "name": name, "created_at": now}


def get_user_by_email(email: str) -> Optional[dict]:
    conn = sqlite3.connect(_get_db_path())
    row = conn.execute("SELECT id, email, name, password_hash, created_at, updated_at FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "email": row[1],
        "name": row[2],
        "password_hash": row[3],
        "created_at": row[4],
        "updated_at": row[5],
    }


def get_user_by_id(user_id: str) -> Optional[dict]:
    conn = sqlite3.connect(_get_db_path())
    row = conn.execute("SELECT id, email, name, password_hash, created_at, updated_at FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "email": row[1],
        "name": row[2],
        "password_hash": row[3],
        "created_at": row[4],
        "updated_at": row[5],
    }


def verify_password(stored_hash: str, password: str) -> bool:
    return hashlib.sha256(password.encode()).hexdigest() == stored_hash
