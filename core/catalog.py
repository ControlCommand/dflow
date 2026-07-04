import json
import uuid
from datetime import datetime
from db.connection import get_connection
from core.state import is_valid_transition, VALID_STATES, TRANSITIONS

def now():
    return datetime.utcnow().isoformat()


def create_do(path, state="INGRESS", lineage=None, do_type="GENERIC", metadata=None):
    """Create a new Data Object in the Catalog."""
    if lineage is None:
        lineage = []
    if metadata is None:
        metadata = {}

    if state not in VALID_STATES:
        raise ValueError(f"Invalid state: {state}. Must be one of {VALID_STATES}")

    conn = get_connection()
    cur = conn.cursor()

    do_id = str(uuid.uuid4())

    try:
        cur.execute("""
            INSERT INTO do_registry
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            do_id,
            state,
            do_type,
            path,
            json.dumps(metadata),
            json.dumps(lineage),
            now(),
            now()
        ))

        conn.commit()
        return do_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_do(do_id):
    """Fetch a Data Object by ID from the Catalog."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM do_registry WHERE id=?", (do_id,))
    row = cur.fetchone()

    conn.close()

    if row is None:
        return None

    # Convert to dict for easier access
    return {
        "id": row[0],
        "state": row[1],
        "type": row[2],
        "path": row[3],
        "metadata": json.loads(row[4]),
        "lineage": json.loads(row[5]),
        "created_at": row[6],
        "updated_at": row[7]
    }


def update_state(do_id, new_state):
    """Update DO state with validation against state machine rules."""
    if new_state not in VALID_STATES:
        raise ValueError(f"Invalid state: {new_state}. Must be one of {VALID_STATES}")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Get current state
        cur.execute("SELECT state FROM do_registry WHERE id=?", (do_id,))
        row = cur.fetchone()

        if row is None:
            raise ValueError(f"Data Object not found: {do_id}")

        current_state = row[0]

        # Validate transition
        if not is_valid_transition(current_state, new_state):
            raise ValueError(
                f"Invalid transition: {current_state} → {new_state}. "
                f"Allowed transitions from {current_state}: {TRANSITIONS.get(current_state, [])}"
            )

        cur.execute("""
            UPDATE do_registry
            SET state=?, updated_at=?
            WHERE id=?
        """, (new_state, now(), do_id))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def append_lineage(child_id, parent_id):
    """Add parent to child's lineage chain in the Catalog."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT lineage FROM do_registry WHERE id=?", (child_id,))
        row = cur.fetchone()

        if row is None:
            raise ValueError(f"Child DO not found: {child_id}")

        lineage = json.loads(row[0])

        if parent_id not in lineage:
            lineage.append(parent_id)

            cur.execute("""
                UPDATE do_registry
                SET lineage=?, updated_at=?
                WHERE id=?
            """, (json.dumps(lineage), now(), child_id))

            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_metadata(do_id, metadata_updates):
    """Update metadata for a Data Object in the Catalog."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT metadata FROM do_registry WHERE id=?", (do_id,))
        row = cur.fetchone()

        if row is None:
            raise ValueError(f"Data Object not found: {do_id}")

        metadata = json.loads(row[0])
        metadata.update(metadata_updates)

        cur.execute("""
            UPDATE do_registry
            SET metadata=?, updated_at=?
            WHERE id=?
        """, (json.dumps(metadata), now(), do_id))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_all_dos():
    """Fetch all Data Objects from the Catalog."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM do_registry ORDER BY created_at DESC")
    rows = cur.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "state": row[1],
            "type": row[2],
            "path": row[3],
            "metadata": json.loads(row[4]),
            "lineage": json.loads(row[5]),
            "created_at": row[6],
            "updated_at": row[7]
        }
        for row in rows
    ]


def validate_lineage_integrity():
    """
    Validate that all lineage references point to existing DOs.
    Returns (is_valid, list_of_errors).
    """
    all_dos = get_all_dos()
    all_ids = {do["id"] for do in all_dos}
    errors = []

    for do_data in all_dos:
        do_id = do_data["id"]
        lineage = do_data["lineage"]

        for parent_id in lineage:
            if parent_id not in all_ids:
                errors.append(f"DO {do_id[:8]}... has broken lineage reference to {parent_id[:8]}...")

    return (len(errors) == 0, errors)


def detect_lineage_cycles():
    """
    Detect cycles in lineage chains.
    Returns (has_cycles, list_of_cycles).
    """
    all_dos = get_all_dos()
    lineage_map = {do["id"]: do["lineage"] for do in all_dos}
    cycles = []

    def dfs(node_id, visited, rec_stack, path):
        visited.add(node_id)
        rec_stack.add(node_id)
        path.append(node_id)

        for parent_id in lineage_map.get(node_id, []):
            if parent_id not in visited:
                cycle = dfs(parent_id, visited, rec_stack, path)
                if cycle:
                    return cycle
            elif parent_id in rec_stack:
                # Found cycle
                cycle_start = path.index(parent_id)
                return path[cycle_start:] + [parent_id]

        path.pop()
        rec_stack.remove(node_id)
        return None

    visited = set()
    for do_id in lineage_map:
        if do_id not in visited:
            cycle = dfs(do_id, visited, set(), [])
            if cycle:
                cycles.append(cycle)

    return (len(cycles) > 0, cycles)