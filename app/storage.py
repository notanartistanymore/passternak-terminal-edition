import sqlite3


DATABASE = "keyholder.db"


def initialize_database(database: str) -> None:
    with sqlite3.connect(database) as db:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keyholder (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                login TEXT NOT NULL,
                password BLOB NOT NULL,
                salt BLOB NOT NULL
            )
        """)
