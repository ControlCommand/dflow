def run(request):
    """
    Classify plugin - simulates classification of LiDAR/engineering data.
    
    Args:
        request: dict with input_path, metadata, parameters
        
    Returns:
        TransformationResponse dict
    """
    print(f"[PLUGIN] classify: {request['input_path']}")
    
    # Simulate classification processing
    return {
        "success": True,
        "output_path": request["input_path"] + ".classified",
        "metadata_updates": {
            "classification_method": "automated",
            "classes_detected": ["ground", "vegetation", "building"]
        },
        "warnings": [],
        "metrics": {
            "runtime_ms": 75,
            "points_processed": 1000000
        }
    }