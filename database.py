# database.py - SQLite SQL Database Layer for ResearchMate AI
import sqlite3
import os
import json
from typing import Optional, Dict, Any, List

DB_PATH = os.path.join(os.path.dirname(__file__), "db", "researchmate.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

# User Helpers
def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def get_or_create_user(username: str, email: str = "", full_name: str = "", avatar_url: str = "", google_id: str = "") -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ? OR (google_id != '' AND google_id = ?)", (username, google_id))
    row = cur.fetchone()
    if row:
        user = dict(row)
        conn.close()
        return user
    
    cur.execute("""
        INSERT INTO users (username, email, full_name, avatar_url, google_id)
        VALUES (?, ?, ?, ?, ?)
    """, (username, email, full_name or username, avatar_url or "/static/images/avatar_default.svg", google_id))
    user_id = cur.lastrowid
    
    cur.execute("""
        INSERT OR IGNORE INTO user_settings (user_id, theme, ollama_host, ollama_model, default_style)
        VALUES (?, 'light', 'https://api.ollama.com', 'llama3.3:70b', 'ieee')
    """, (user_id,))
    
    conn.commit()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = dict(cur.fetchone())
    conn.close()
    return user

def update_user_profile(user_id: int, full_name: str, email: str, avatar_url: str = ""):
    conn = get_db_connection()
    cur = conn.cursor()
    if avatar_url:
        cur.execute("UPDATE users SET full_name = ?, email = ?, avatar_url = ? WHERE id = ?", (full_name, email, avatar_url, user_id))
    else:
        cur.execute("UPDATE users SET full_name = ?, email = ? WHERE id = ?", (full_name, email, user_id))
    conn.commit()
    conn.close()

# Settings Helpers
def get_user_settings(user_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute("""
            INSERT OR IGNORE INTO user_settings (user_id, theme, ollama_host, ollama_model, default_style)
            VALUES (?, 'light', 'https://api.ollama.com', 'llama3.3:70b', 'ieee')
        """, (user_id,))
        conn.commit()
        cur.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
    conn.close()
    return dict(row) if row else {}

def update_user_settings(user_id: int, theme: str = "light", ollama_host: str = "", ollama_model: str = "", ollama_api_key: str = "", default_style: str = "ieee", google_client_id: str = ""):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_settings (user_id, theme, ollama_host, ollama_model, ollama_api_key, default_style, google_client_id, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            theme = excluded.theme,
            ollama_host = excluded.ollama_host,
            ollama_model = excluded.ollama_model,
            ollama_api_key = excluded.ollama_api_key,
            default_style = excluded.default_style,
            google_client_id = excluded.google_client_id,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, theme, ollama_host, ollama_model, ollama_api_key, default_style, google_client_id))
    conn.commit()
    conn.close()

# History Helpers
def add_history(user_id: int, feature: str, title: str, summary: str = "", meta: dict = None, file_path: str = "") -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    meta_json = json.dumps(meta or {})
    cur.execute("""
        INSERT INTO history (user_id, feature, title, summary, meta_json, file_path)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, feature, title, summary, meta_json, file_path))
    item_id = cur.lastrowid
    conn.commit()
    conn.close()
    return item_id

def get_user_history(user_id: int, feature: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    if feature and feature != "all":
        cur.execute("SELECT * FROM history WHERE user_id = ? AND feature = ? ORDER BY created_at DESC LIMIT ?", (user_id, feature, limit))
    else:
        cur.execute("SELECT * FROM history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
    rows = cur.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["meta"] = json.loads(d["meta_json"]) if d.get("meta_json") else {}
        except Exception:
            d["meta"] = {}
        result.append(d)
    return result

def delete_history_item(user_id: int, item_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM history WHERE id = ? AND user_id = ?", (item_id, user_id))
    conn.commit()
    conn.close()

def clear_user_history(user_id: int, feature: Optional[str] = None):
    conn = get_db_connection()
    cur = conn.cursor()
    if feature and feature != "all":
        cur.execute("DELETE FROM history WHERE user_id = ? AND feature = ?", (user_id, feature))
    else:
        cur.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Saved Papers Helpers
def save_paper(user_id: int, paper: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO saved_papers (user_id, title, authors, year, venue, abstract, url, pdf_url, doi, bibtex)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        paper.get("title", ""),
        paper.get("authors", ""),
        paper.get("year", 2026),
        paper.get("venue", ""),
        paper.get("abstract", ""),
        paper.get("url", ""),
        paper.get("pdf_url", ""),
        paper.get("doi", ""),
        paper.get("bibtex", "")
    ))
    saved_id = cur.lastrowid
    conn.commit()
    conn.close()
    return saved_id

def get_saved_papers(user_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM saved_papers WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_saved_paper(user_id: int, paper_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM saved_papers WHERE id = ? AND user_id = ?", (paper_id, user_id))
    conn.commit()
    conn.close()

# Saved Ideas Helpers
def save_idea(user_id: int, idea: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO saved_ideas (user_id, title, domain, hypothesis, methodology, novelty, full_content_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        idea.get("title", "Innovative Research Proposal"),
        idea.get("domain", ""),
        idea.get("hypothesis", ""),
        idea.get("methodology", ""),
        idea.get("novelty", ""),
        json.dumps(idea)
    ))
    saved_id = cur.lastrowid
    conn.commit()
    conn.close()
    return saved_id

def get_saved_ideas(user_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM saved_ideas WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        try:
            d["full_content"] = json.loads(d["full_content_json"]) if d.get("full_content_json") else {}
        except Exception:
            d["full_content"] = {}
        res.append(d)
    return res

def delete_saved_idea(user_id: int, idea_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM saved_ideas WHERE id = ? AND user_id = ?", (idea_id, user_id))
    conn.commit()
    conn.close()

# Saved Conferences Helpers
def save_conference(user_id: int, conf: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO saved_conferences (user_id, acronym, name, venue, deadline, conference_date, core_rank, url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        conf.get("acronym", ""),
        conf.get("name", ""),
        conf.get("venue", ""),
        conf.get("deadline", ""),
        conf.get("conference_date", ""),
        conf.get("core_rank", ""),
        conf.get("url", "")
    ))
    saved_id = cur.lastrowid
    conn.commit()
    conn.close()
    return saved_id

def get_saved_conferences(user_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM saved_conferences WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_saved_conference(user_id: int, conf_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM saved_conferences WHERE id = ? AND user_id = ?", (conf_id, user_id))
    conn.commit()
    conn.close()

# User Stats
def get_user_stats(user_id: int) -> Dict[str, int]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM history WHERE user_id = ? AND feature = 'formatter'", (user_id,))
    papers_formatted = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM history WHERE user_id = ? AND feature = 'slides'", (user_id,))
    slides_generated = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM saved_papers WHERE user_id = ?", (user_id,))
    saved_papers_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM saved_ideas WHERE user_id = ?", (user_id,))
    saved_ideas_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM saved_conferences WHERE user_id = ?", (user_id,))
    saved_conferences_count = cur.fetchone()[0]
    
    conn.close()
    return {
        "papers_formatted": papers_formatted,
        "slides_generated": slides_generated,
        "saved_papers": saved_papers_count,
        "saved_ideas": saved_ideas_count,
        "saved_conferences": saved_conferences_count
    }
