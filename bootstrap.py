import os
from db.connection import get_connection

FOLDERS = [
    "storage/ingress",
    "storage/active",
    "storage/scratch",
    "storage/curated",
    "storage/archive"
]

def init_storage():
    for f in FOLDERS:
        os.makedirs(f, exist_ok=True)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    with open("db/schema.sql", "r") as f:
        cur.executescript(f.read())

    conn.commit()
    conn.close()

def initialize():
    init_storage()
    init_db()
    print("[BOOTSTRAP] Initialized DB and storage")