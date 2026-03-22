import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger('Memory')
DB_PATH = Path.home() / '.jarvis' / 'memory.db'

class Memory:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._init_db()
        logger.info(f"💾 Memory initialized")
    
    def _init_db(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);
        """)
        self.conn.commit()
    
    def save_message(self, chat_id, role, content):
        self.conn.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)", (chat_id, role, content))
        self.conn.commit()
    
    def get_history(self, chat_id, limit=20):
        cursor = self.conn.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY timestamp DESC LIMIT ?", (chat_id, limit))
        return [{"role": r[0], "content": r[1]} for r in reversed(cursor.fetchall())]
    
    def remember(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO facts (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()
    
    def clear_history(self, chat_id):
        self.conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        self.conn.commit()
    
    def get_pending_tasks(self):
        cursor = self.conn.execute("SELECT id, title, details FROM tasks WHERE status = 'pending'")
        return [{"id": r[0], "title": r[1], "details": r[2]} for r in cursor.fetchall()]
