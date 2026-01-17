"""
Database configuration and initialization
"""

from sqlite_worker import SqliteWorker
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

_worker = None


def get_worker() -> SqliteWorker:
    """Get database worker instance (singleton)"""
    global _worker
    if _worker is None:
        _worker = SqliteWorker(
            DB_PATH,
            execute_init=[
                "PRAGMA journal_mode=WAL;",
                "PRAGMA synchronous=NORMAL;",
                "PRAGMA temp_store=MEMORY;"
            ],
            max_count=50
        )
    return _worker


def init_database():
    """Initialize database schema"""
    worker = get_worker()
    
    # Create your tables here
    worker.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            value REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    worker.execute("""
        CREATE INDEX IF NOT EXISTS idx_items_created 
        ON items(created_at)
    """)
