from core.plugin_runner import run_plugin
from events.bus import emit

def execute_pipeline(do_id, file_path):
    """Execute the pipeline on a given file."""
    # Emit pipeline start event
    emit("PIPELINE_STARTED", {"do_id": do_id, "input_path": file_path})
    
    request = {
        "input_path": file_path,
        "metadata": {},
        "parameters": {}
    }
    
    result = run_plugin("denoise", request)
    
    if result.get("success"):
        emit("TRANSFORM_APPLIED", {
            "do_id": do_id,
            "plugin": "denoise",
            "output_path": result.get("output_path"),
            "metrics": result.get("metrics", {})
        })
    
    emit("PIPELINE_FINISHED", {
        "do_id": do_id,
        "success": result.get("success", False),
        "output_path": result.get("output_path")
    })
    
    return result