from core.catalog import create_do, append_lineage, update_state, get_do
from core.pipeline import execute_pipeline
from core.state import is_valid_transition, get_allowed_transitions
from events.bus import emit


def ingest(file_path):
    """Ingest a file into the system, creating a new Data Object."""
    emit("INGEST_STARTED", {"input_path": file_path})
    
    do_id = create_do(file_path, state="INGRESS")
    
    emit("DO_CREATED", {"do_id": do_id, "state": "INGRESS", "path": file_path})
    emit("INGEST_COMPLETED", {"do_id": do_id})
    
    return do_id


def run(do_id, file_path):
    """
    Execute workflow on a Data Object.
    
    Flow:
    1. Validate current state allows processing
    2. Run pipeline
    3. Create child DO from result
    4. Update lineage
    5. Transition parent to CURATED
    """
    # Get current DO state
    parent_do = get_do(do_id)
    if parent_do is None:
        raise ValueError(f"Data Object not found: {do_id}")
    
    current_state = parent_do["state"]
    
    # Validate that we can process from this state
    # INGRESS -> VALIDATED -> ACTIVE is the normal flow
    # For simplicity, we allow processing from INGRESS or VALIDATED
    if current_state not in ["INGRESS", "VALIDATED", "ACTIVE"]:
        raise ValueError(
            f"Cannot run pipeline on DO in state: {current_state}. "
            f"Allowed transitions: {get_allowed_transitions(current_state)}"
        )
    
    # STEP 1 — run pipeline
    result = execute_pipeline(do_id, file_path)
    
    if not result.get("success"):
        emit("VALIDATION_FAILED", {
            "do_id": do_id,
            "reason": "Pipeline execution failed",
            "warnings": result.get("warnings", [])
        })
        raise RuntimeError(f"Pipeline failed: {result.get('warnings', ['Unknown error'])}")
    
    # STEP 2 — create new DO from result (child DO)
    child_id = create_do(
        path=result["output_path"],
        state="ACTIVE",
        lineage=[do_id],
        metadata=result.get("metadata_updates", {})
    )
    
    emit("DO_CREATED", {
        "do_id": child_id,
        "state": "ACTIVE",
        "path": result["output_path"],
        "parent_id": do_id
    })
    
    # STEP 3 — update lineage (already set during creation, but ensure consistency)
    append_lineage(child_id, do_id)
    
    # STEP 4 — transition parent state through VALIDATED to CURATED
    # First transition to VALIDATED if currently INGRESS
    if current_state == "INGRESS":
        update_state(do_id, "VALIDATED")
        emit("STATE_CHANGED", {"do_id": do_id, "from": "INGRESS", "to": "VALIDATED"})
        
        update_state(do_id, "ACTIVE")
        emit("STATE_CHANGED", {"do_id": do_id, "from": "VALIDATED", "to": "ACTIVE"})
    
    # Then transition to CURATED
    update_state(do_id, "CURATED")
    emit("STATE_CHANGED", {"do_id": do_id, "from": current_state, "to": "CURATED"})
    
    return child_id, result