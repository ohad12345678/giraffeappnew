import sqlite3
from contextlib import contextmanager

DATABASE_NAME = "giraffe_quality.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    with get_db() as db:
        cursor = db.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                branch TEXT NOT NULL,
                role TEXT DEFAULT 'branch'
            )
        """)
        
        # Quality checks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch TEXT NOT NULL,
                dish_name TEXT NOT NULL,
                chef_name TEXT NOT NULL,
                rating INTEGER NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL
            )
        """)
        
        db.commit()
