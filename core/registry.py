import json
import uuid
from datetime import datetime
from db.connection import get_connection

def now():
    return datetime.utcnow().isoformat()


def create_do(path, state="INGRESS", lineage=None):
    if lineage is None:
        lineage = []

    conn = get_connection()
    cur = conn.cursor()

    do_id = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO do_registry
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        do_id,
        state,
        "GENERIC",
        path,
        json.dumps({}),
        json.dumps(lineage),
        now(),
        now()
    ))

    conn.commit()
    conn.close()

    return do_id


def get_do(do_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM do_registry WHERE id=?", (do_id,))
    row = cur.fetchone()

    conn.close()
    return row


def update_state(do_id, state):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE do_registry
        SET state=?, updated_at=?
        WHERE id=?
    """, (state, now(), do_id))

    conn.commit()
    conn.close()


def append_lineage(child_id, parent_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT lineage FROM do_registry WHERE id=?", (child_id,))
    row = cur.fetchone()

    lineage = json.loads(row[0])
    lineage.append(parent_id)

    cur.execute("""
        UPDATE do_registry
        SET lineage=?
        WHERE id=?
    """, (json.dumps(lineage), child_id))

    conn.commit()
    conn.close()