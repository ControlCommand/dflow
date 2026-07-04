from core.plugin_runner import run_plugin

def execute_pipeline(do_id, file_path):
    request = {
        "input_path": file_path,
        "metadata": {},
        "parameters": {}
    }

    result = run_plugin("denoise", request)

    return result