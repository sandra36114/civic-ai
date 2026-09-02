import sqlite3

DATABASE = "civicai.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'citizen'
        )
    """)

    # Complaints table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            category TEXT DEFAULT 'Pending',
            urgency TEXT DEFAULT 'Pending',
            priority INTEGER DEFAULT 0,
            credibility INTEGER DEFAULT 0,
            is_duplicate INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Submitted',
            department TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()