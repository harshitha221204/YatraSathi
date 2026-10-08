import sqlite3

DATABASE = "yatrasathi.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_users_table():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def create_trips_table():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            destination TEXT NOT NULL,
            days INTEGER NOT NULL,
            travelers INTEGER NOT NULL,
            budget INTEGER NOT NULL,
            interests TEXT,
            style TEXT
        )
    """)

    conn.commit()
    conn.close()