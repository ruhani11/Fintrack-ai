import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.db")

if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print("Old database deleted.")

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        date TEXT NOT NULL,
        month TEXT NOT NULL
    )
    """
)

conn.commit()
conn.close()

print("New database and table created successfully.")