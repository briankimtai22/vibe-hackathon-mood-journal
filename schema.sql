CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    emotion_label TEXT,
    emotion_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);