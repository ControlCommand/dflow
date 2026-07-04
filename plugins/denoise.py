def run(request):
    print(f"[PLUGIN] denoise: {request['input_path']}")

    return {
        "success": True,
        "output_path": request["input_path"] + ".denoised",
        "metadata_updates": {},
        "warnings": [],
        "metrics": {
            "runtime_ms": 50
        }
    }