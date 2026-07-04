import json
import uuid
from datetime import datetime
from db.connection import get_connection
from core.state import is_valid_transition, VALID_STATES, TRANSITIONS

def now():
    return datetime.utcnow().isoformat()


def create_do(path, state="INGRESS", lineage=None, do_type="GENERIC", metadata=None):
    """Create a new Data Object in the registry."""
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
    """Fetch a Data Object by ID."""
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
    """Add parent to child's lineage chain."""
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
    """Update metadata for a Data Object."""
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
    """Fetch all Data Objects from registry."""
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