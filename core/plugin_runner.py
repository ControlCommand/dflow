import importlib

def run_plugin(name, request):
    module = importlib.import_module(f"plugins.{name}")
    return module.run(request)