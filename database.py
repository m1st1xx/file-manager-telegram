import sqlite3
from contextlib import contextmanager
from config import NEW_DB_PATH, OLD_DB_PATH

@contextmanager
def connection(path):
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def get_user_by_username(username):
    with connection(NEW_DB_PATH) as db:
        return db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

def get_user_by_id(user_id):
    with connection(NEW_DB_PATH) as db:
        return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

def get_user_by_folder(folder_path):
    with connection(NEW_DB_PATH) as db:
        row = db.execute("SELECT * FROM users WHERE folder_path = ?", (folder_path,)).fetchone()
        if row:
            return row
    with connection(OLD_DB_PATH) as db:
        return db.execute("SELECT * FROM users WHERE folder_path = ?", (folder_path,)).fetchone()

def add_user(username, password_hash, folder_path):
    with connection(NEW_DB_PATH) as db:
        cursor = db.execute(
            "INSERT INTO users (username, password_hash, folder_path) VALUES (?, ?, ?)",
            (username, password_hash, str(folder_path))
        )
        return cursor.lastrowid

def get_subjects(user_id):
    with connection(NEW_DB_PATH) as db:
        return db.execute(
            "SELECT name FROM subjects WHERE user_id = ? ORDER BY id", (user_id,)
        ).fetchall()

def subject_exists(user_id, subject):
    with connection(NEW_DB_PATH) as db:
        return db.execute(
            "SELECT 1 FROM subjects WHERE user_id = ? AND name = ?", (user_id, subject)
        ).fetchone() is not None

def add_subject(user_id, subject):
    with connection(NEW_DB_PATH) as db:
        db.execute("INSERT INTO subjects (user_id, name) VALUES (?, ?)", (user_id, subject))

def delete_subject(user_id, subject):
    with connection(NEW_DB_PATH) as db:
        db.execute("DELETE FROM subjects WHERE user_id = ? AND name = ?", (user_id, subject))