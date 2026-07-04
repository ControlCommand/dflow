"""
Catalog Query Engine for DFlow - Deterministic query functions for Data Objects.
RFC-0008: Query Layer

All queries use parameterized SQL to prevent injection attacks.
No string concatenation in SQL queries.
"""

from db.connection import get_connection
import json


def filter_by_state(state: str):
    """
    Filter Data Objects by state.
    Uses parameterized query for safety.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT * FROM do_registry
        WHERE state = ?
    """, (state,))
    
    rows = cur.fetchall()
    conn.close()
    
    return [_row_to_dict(row) for row in rows]


def filter_by_path(substring: str):
    """
    Filter Data Objects by path substring.
    Uses parameterized query with LIKE for safe pattern matching.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Safe pattern matching - escape special LIKE characters
    escaped = substring.replace('%', '\\%').replace('_', '\\_')
    pattern = f"%{escaped}%"
    
    cur.execute("""
        SELECT * FROM do_registry
        WHERE path LIKE ? ESCAPE '\\'
    """, (pattern,))
    
    rows = cur.fetchall()
    conn.close()
    
    return [_row_to_dict(row) for row in rows]


def filter_by_time_range(start: str, end: str):
    """
    Filter Data Objects by creation time range.
    Expects ISO format timestamps.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT * FROM do_registry
        WHERE created_at >= ? AND created_at <= ?
        ORDER BY created_at DESC
    """, (start, end))
    
    rows = cur.fetchall()
    conn.close()
    
    return [_row_to_dict(row) for row in rows]


def search_metadata(key: str, value):
    """
    Search Data Objects by metadata key-value pair.
    Safely parses JSON metadata and searches for matches.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM do_registry")
    rows = cur.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        try:
            metadata = json.loads(row[4])  # metadata is at index 4
            if key in metadata and metadata[key] == value:
                results.append(_row_to_dict(row))
        except (json.JSONDecodeError, TypeError):
            # Skip records with invalid metadata
            continue
    
    return results


def get_ancestors(do_id: str):
    """
    Get all ancestors (parents, grandparents, etc.) of a Data Object.
    Traverses lineage chain recursively.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Get the DO's lineage
    cur.execute("SELECT lineage FROM do_registry WHERE id = ?", (do_id,))
    row = cur.fetchone()
    
    if row is None:
        conn.close()
        return []
    
    lineage = json.loads(row[0])
    conn.close()
    
    # Recursively get ancestors
    all_ancestors = []
    visited = set()
    
    def traverse(parent_ids):
        for parent_id in parent_ids:
            if parent_id in visited:
                continue
            visited.add(parent_id)
            all_ancestors.append(parent_id)
            
            # Get parent's lineage
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT lineage FROM do_registry WHERE id = ?", (parent_id,))
            parent_row = cur.fetchone()
            conn.close()
            
            if parent_row:
                parent_lineage = json.loads(parent_row[0])
                traverse(parent_lineage)
    
    traverse(lineage)
    return all_ancestors


def get_descendants(do_id: str):
    """
    Get all descendants (children, grandchildren, etc.) of a Data Object.
    Queries catalog to find all DOs that have this DO in their lineage.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, lineage FROM do_registry")
    all_rows = cur.fetchall()
    conn.close()
    
    descendants = []
    target_id = do_id
    
    for row in all_rows:
        child_id = row[0]
        lineage = json.loads(row[1])
        
        if target_id in lineage:
            descendants.append(child_id)
    
    return descendants


def get_siblings(do_id: str):
    """
    Get all siblings (DOs with same parents) of a Data Object.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Get target DO's lineage
    cur.execute("SELECT lineage FROM do_registry WHERE id = ?", (do_id,))
    row = cur.fetchone()
    
    if row is None:
        conn.close()
        return []
    
    my_lineage = json.loads(row[0])
    my_lineage_set = set(my_lineage)
    
    # Find all DOs with same lineage
    cur.execute("SELECT id, lineage FROM do_registry")
    all_rows = cur.fetchall()
    conn.close()
    
    siblings = []
    for row in all_rows:
        other_id = row[0]
        if other_id == do_id:
            continue
        
        other_lineage = json.loads(row[1])
        if set(other_lineage) == my_lineage_set:
            siblings.append(other_id)
    
    return siblings


def full_text_search(query: str):
    """
    Perform full-text search across path, state, type, and metadata.
    Simple implementation using LIKE patterns.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Escape special LIKE characters
    escaped = query.replace('%', '\\%').replace('_', '\\_')
    pattern = f"%{escaped}%"
    
    cur.execute("""
        SELECT * FROM do_registry
        WHERE path LIKE ? ESCAPE '\\'
           OR state LIKE ? ESCAPE '\\'
           OR type LIKE ? ESCAPE '\\'
           OR metadata LIKE ? ESCAPE '\\'
        ORDER BY created_at DESC
    """, (pattern, pattern, pattern, pattern))
    
    rows = cur.fetchall()
    conn.close()
    
    return [_row_to_dict(row) for row in rows]


def _row_to_dict(row):
    """Convert a database row to a dictionary."""
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
