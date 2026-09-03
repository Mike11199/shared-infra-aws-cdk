import importlib.util
from pathlib import Path


def test_app_binds_all_stacks_to_cli_environment(monkeypatch):
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")
    monkeypatch.setenv("CDK_DEFAULT_REGION", "us-west-1")

    app_path = Path(__file__).resolve().parents[2] / "app.py"
    spec = importlib.util.spec_from_file_location("shared_infra_app_test", app_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for stack in (
        module.network_stack,
        module.hosted_zones_stack,
        module.certificates_stack,
        module.domain_exports_stack,
        module.infrastructure_stack,
    ):
        assert stack.account == "123456789012"
        assert stack.region == "us-west-1"
