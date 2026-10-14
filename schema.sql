-- ResearchMate AI SQL Database Schema
-- Pure standard SQL for SQLite3

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    full_name TEXT,
    avatar_url TEXT,
    role TEXT DEFAULT 'researcher',
    google_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    theme TEXT DEFAULT 'light',
    ollama_host TEXT DEFAULT 'https://api.ollama.com',
    ollama_model TEXT DEFAULT 'llama3.3:70b',
    ollama_api_key TEXT DEFAULT '',
    default_style TEXT DEFAULT 'ieee',
    google_client_id TEXT DEFAULT '',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    feature TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    meta_json TEXT,
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS saved_papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    authors TEXT,
    year INTEGER,
    venue TEXT,
    abstract TEXT,
    url TEXT,
    pdf_url TEXT,
    doi TEXT,
    bibtex TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS saved_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    domain TEXT,
    hypothesis TEXT,
    methodology TEXT,
    novelty TEXT,
    full_content_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS saved_conferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    acronym TEXT NOT NULL,
    name TEXT NOT NULL,
    venue TEXT,
    deadline TEXT,
    conference_date TEXT,
    core_rank TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Seed Default Guest and Demo User
INSERT OR IGNORE INTO users (id, username, email, full_name, avatar_url, role)
VALUES (1, 'guest', 'guest@researchmate.ai', 'Guest Scholar', '/static/images/avatar_default.svg', 'guest');

INSERT OR IGNORE INTO user_settings (user_id, theme, ollama_host, ollama_model, default_style)
VALUES (1, 'light', 'https://api.ollama.com', 'llama3.3:70b', 'ieee');
