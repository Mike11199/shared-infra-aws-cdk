"""Deployment workflow regression tests."""

from pathlib import Path


WORKFLOW = Path(__file__).parents[2] / ".github/workflows/deploy-shared-infrastructure.yml"


def test_shared_stacks_deploy_once_in_explicit_order_with_drift_repair():
    """Each stack deploys alone while retaining drift-aware updates."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    deploy_block = workflow[workflow.index("cdk deploy SharedNetworkStack") :]
    commands = [line.strip() for line in deploy_block.splitlines() if "cdk deploy" in line]

    assert [command.split()[2] for command in commands] == [
        "SharedNetworkStack",
        "SharedHostedZonesStack",
        "SharedCertificatesStack",
        "SharedDomainsStack",
        "SharedInfrastructureStack",
    ]
    assert all("--exclusively" in command for command in commands)
    assert all("--revert-drift" in command for command in commands)