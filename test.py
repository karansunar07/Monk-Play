from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

app_path = Path(__file__).with_name("app.py")
spec = spec_from_file_location("project_app", app_path)
module = module_from_spec(spec)
spec.loader.exec_module(module)
app = module.app


def run_smoke_tests():
    client = app.test_client()

    for route in ("/", "/login", "/register"):
        response = client.get(route)
        print(f"{route}: {response.status_code}")


if __name__ == "__main__":
    run_smoke_tests()
