# backend/db.py
import sqlite3
from pathlib import Path
from datetime import datetime
import json

DB_PATH = Path(__file__).parent / "interview.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # Answers table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp TEXT,
            question TEXT,
            answer TEXT,
            score INTEGER,
            feedback TEXT
        )
        """
    )
    # Users table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            hashed_password TEXT,
            created_at TEXT
        )
        """
    )
    # User Sessions table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER,
            resume_text TEXT,
            skills TEXT,
            rag_path TEXT,
            history TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )
    conn.commit()
    conn.close()

# --- Answer Management ---
def save_answer(session_id: str, question: str, answer: str, score: int, feedback: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO answers (session_id, timestamp, question, answer, score, feedback)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (session_id, datetime.utcnow().isoformat(), question, answer, score, feedback),
    )
    conn.commit()
    conn.close()

def get_session_summary(session_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT question, answer, score, feedback FROM answers WHERE session_id = ?",
        (session_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- User Management ---
def create_user(username, email, hashed_password):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, email, hashed_password, created_at) VALUES (?, ?, ?, ?)",
            (username, email, hashed_password, datetime.utcnow().isoformat())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

# --- Session Management ---
def save_session(session_id, user_id, resume_text, skills, rag_path, history):
    conn = get_conn()
    cur = conn.cursor()
    skills_json = json.dumps(skills)
    history_json = json.dumps(history)
    cur.execute(
        """
        INSERT OR REPLACE INTO user_sessions (session_id, user_id, resume_text, skills, rag_path, history, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (session_id, user_id, resume_text, skills_json, rag_path, history_json, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def get_user_sessions(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT session_id, created_at FROM user_sessions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_session_details(session_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_sessions WHERE session_id = ?", (session_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["skills"] = json.loads(d["skills"])
        d["history"] = json.loads(d["history"])
        return d
    return None
