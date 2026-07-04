from core.registry import create_do, append_lineage, update_state
from core.pipeline import execute_pipeline


def ingest(file_path):
    do_id = create_do(file_path, state="INGRESS")
    return do_id


def run(do_id, file_path):
    # STEP 1 — run pipeline
    result = execute_pipeline(do_id, file_path)

    # STEP 2 — create new DO from result
    child_id = create_do(
        path=result["output_path"],
        state="ACTIVE",
        lineage=[do_id]
    )

    # STEP 3 — update parent-child lineage
    append_lineage(child_id, do_id)

    # STEP 4 — update states
    update_state(do_id, "CURATED")
    update_state(child_id, "ACTIVE")

    return child_id, result