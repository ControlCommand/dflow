"""
Lifecycle Control Engine for DFlow - Safe state transitions with transactional guarantees.
RFC-0009: Lifecycle Management

All state changes MUST go through this module.
NO direct state mutation outside lifecycle engine.
EVERY transition must be logged.
"""

from core.state import VALID_STATES, TRANSITIONS, is_valid_transition
from core.catalog import get_do, update_state as catalog_update_state
from events.bus import emit


# State transition rules (imported from core.state for reference)
# These are strictly enforced by the lifecycle engine
ALLOWED_TRANSITIONS = TRANSITIONS


class LifecycleError(Exception):
    """Exception raised for invalid lifecycle transitions."""
    pass


def transition(do_id: str, new_state: str, reason: str = None):
    """
    Perform a safe state transition for a Data Object.
    
    Args:
        do_id: The Data Object ID to transition
        new_state: The target state
        reason: Optional reason for the transition (for audit trail)
    
    Raises:
        LifecycleError: If the transition is not allowed
        ValueError: If the DO does not exist
    """
    # Validate new state
    if new_state not in VALID_STATES:
        raise LifecycleError(f"Invalid state: {new_state}. Must be one of {VALID_STATES}")
    
    # Get current DO state
    record = get_do(do_id)
    if record is None:
        raise ValueError(f"Data Object not found: {do_id}")
    
    current_state = record["state"]
    
    # Validate transition
    if not is_valid_transition(current_state, new_state):
        allowed = TRANSITIONS.get(current_state, [])
        raise LifecycleError(
            f"Invalid transition: {current_state} → {new_state}. "
            f"Allowed transitions from {current_state}: {allowed}"
        )
    
    # Perform the state update
    catalog_update_state(do_id, new_state)
    
    # Log the transition event
    emit("STATE_CHANGED", {
        "do_id": do_id,
        "from_state": current_state,
        "to_state": new_state,
        "reason": reason
    })
    
    return {
        "do_id": do_id,
        "from_state": current_state,
        "to_state": new_state,
        "reason": reason
    }


def archive(do_id: str, reason: str = None):
    """
    Archive a Data Object for long-term storage.
    Transitions to ARCHIVED state (terminal state).
    
    Args:
        do_id: The Data Object ID to archive
        reason: Optional reason for archival
    """
    if reason is None:
        reason = "user archive"
    
    return transition(do_id, "ARCHIVED", reason)


def reject(do_id: str, reason: str = None):
    """
    Reject a Data Object (soft delete).
    Transitions to REJECTED state (terminal state).
    
    This is the preferred method for deletion - data is preserved
    but marked as invalid/unused.
    
    Args:
        do_id: The Data Object ID to reject
        reason: Optional reason for rejection
    """
    if reason is None:
        reason = "user delete"
    
    return transition(do_id, "REJECTED", reason)


def validate(do_id: str, reason: str = None):
    """
    Validate a Data Object.
    Transitions from INGRESS to VALIDATED.
    
    Args:
        do_id: The Data Object ID to validate
        reason: Optional reason for validation
    """
    if reason is None:
        reason = "manual validation"
    
    return transition(do_id, "VALIDATED", reason)


def activate(do_id: str, reason: str = None):
    """
    Activate a Data Object.
    Transitions from VALIDATED to ACTIVE.
    
    Args:
        do_id: The Data Object ID to activate
        reason: Optional reason for activation
    """
    if reason is None:
        reason = "manual activation"
    
    return transition(do_id, "ACTIVE", reason)


def curate(do_id: str, reason: str = None):
    """
    Curate a Data Object.
    Transitions from ACTIVE to CURATED.
    
    Args:
        do_id: The Data Object ID to curate
        reason: Optional reason for curation
    """
    if reason is None:
        reason = "manual curation"
    
    return transition(do_id, "CURATED", reason)


def scratch(do_id: str, reason: str = None):
    """
    Move a Data Object to scratch/workspace state.
    Transitions from ACTIVE to SCRATCH.
    
    Args:
        do_id: The Data Object ID to move to scratch
        reason: Optional reason for scratch status
    """
    if reason is None:
        reason = "temporary workspace"
    
    return transition(do_id, "SCRATCH", reason)


def restore_from_scratch(do_id: str, reason: str = None):
    """
    Restore a Data Object from scratch to active.
    Transitions from SCRATCH to ACTIVE.
    
    Args:
        do_id: The Data Object ID to restore
        reason: Optional reason for restoration
    """
    if reason is None:
        reason = "restored from scratch"
    
    return transition(do_id, "ACTIVE", reason)


def restore_from_archived(do_id: str, reason: str = None):
    """
    Restore a Data Object from archived to active.
    Transitions from ARCHIVED to ACTIVE.
    
    Note: According to state machine, ARCHIVED has no allowed transitions.
    This function will raise LifecycleError if called.
    Use only if state machine rules are updated.
    
    Args:
        do_id: The Data Object ID to restore
        reason: Optional reason for restoration
    """
    if reason is None:
        reason = "restored from archive"
    
    # This will fail per state machine rules - ARCHIVED is terminal
    return transition(do_id, "ACTIVE", reason)


def get_allowed_next_states(do_id: str):
    """
    Get the list of allowed next states for a Data Object.
    
    Args:
        do_id: The Data Object ID
    
    Returns:
        List of allowed state names
    """
    record = get_do(do_id)
    if record is None:
        return []
    
    current_state = record["state"]
    return TRANSITIONS.get(current_state, [])


def can_transition(do_id: str, to_state: str):
    """
    Check if a Data Object can transition to a given state.
    
    Args:
        do_id: The Data Object ID
        to_state: The target state
    
    Returns:
        Boolean indicating if transition is allowed
    """
    record = get_do(do_id)
    if record is None:
        return False
    
    current_state = record["state"]
    return is_valid_transition(current_state, to_state)


def get_lifecycle_history(do_id: str):
    """
    Get the lifecycle history for a Data Object from events table.
    
    Args:
        do_id: The Data Object ID
    
    Returns:
        List of state change events
    """
    from db.connection import get_connection
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT event, timestamp, do_id
        FROM events
        WHERE do_id = ? AND event = 'STATE_CHANGED'
        ORDER BY timestamp ASC
    """, (do_id,))
    
    rows = cur.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        try:
            import json
            payload = json.loads(row[0]) if isinstance(row[0], str) else {}
        except:
            payload = {}
        
        history.append({
            "event": row[0],
            "timestamp": row[1],
            "do_id": row[2]
        })
    
    return history
