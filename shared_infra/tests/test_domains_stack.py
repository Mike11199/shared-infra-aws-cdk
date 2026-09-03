from aws_cdk import App

from shared_infra.certificates_stack import SharedCertificatesStack
from shared_infra.domain_exports_stack import SharedDomainExportsStack
from shared_infra.hosted_zones_stack import SharedHostedZonesStack


def synthesized(stack_type, stack_name: str) -> dict:
    app = App()
    stack = stack_type(app, stack_name)
    return app.synth().get_stack_by_name(stack.stack_name).template


def resources(cloudformation: dict, resource_type: str) -> list[dict]:
    return [
        resource
        for resource in cloudformation["Resources"].values()
        if resource["Type"] == resource_type
    ]


def test_hosted_zone_stack_owns_three_retained_zones_only():
    cloudformation = synthesized(SharedHostedZonesStack, "TestSharedHostedZonesStack")
    assert set(cloudformation["Resources"]) == {
        "AlpinePeakHostedZone",
        "PortfolioHostedZone",
        "MachineLearningHostedZone",
    }
    assert resources(cloudformation, "AWS::CertificateManager::Certificate") == []
    for resource in cloudformation["Resources"].values():
        assert resource["DeletionPolicy"] == "Retain"
        assert resource["UpdateReplacePolicy"] == "Retain"


def test_hosted_zone_stack_exports_generated_zone_ids():
    outputs = synthesized(SharedHostedZonesStack, "TestSharedHostedZonesStack")["Outputs"]
    for resource_id in ("AlpinePeak", "Portfolio", "MachineLearning"):
        assert outputs[f"{resource_id}HostedZoneId"] == {
            "Value": {"Ref": f"{resource_id}HostedZone"},
            "Export": {"Name": f"SharedOwned{resource_id}HostedZoneId"},
        }


def test_certificate_stack_uses_hosted_zone_exports_not_physical_ids():
    cloudformation = synthesized(SharedCertificatesStack, "TestSharedCertificatesStack")
    assert resources(cloudformation, "AWS::Route53::HostedZone") == []
    certificates = resources(
        cloudformation, "AWS::CertificateManager::Certificate"
    )
    assert len(certificates) == 3

    for resource_id, resource in zip(
        ("AlpinePeak", "Portfolio", "MachineLearning"), certificates
    ):
        validation = resource["Properties"]["DomainValidationOptions"][0]
        assert validation["HostedZoneId"] == {
            "Fn::ImportValue": f"SharedOwned{resource_id}HostedZoneId"
        }
        assert resource["DeletionPolicy"] == "Retain"
        assert resource["UpdateReplacePolicy"] == "Retain"


def test_certificate_stack_exports_generated_certificate_arns():
    outputs = synthesized(SharedCertificatesStack, "TestSharedCertificatesStack")[
        "Outputs"
    ]
    for resource_id in ("AlpinePeak", "Portfolio", "MachineLearning"):
        assert outputs[f"{resource_id}CertificateArn"] == {
            "Value": {"Ref": f"{resource_id}Certificate"},
            "Export": {"Name": f"SharedOwned{resource_id}CertificateArn"},
        }


def test_domain_export_bridge_preserves_public_export_names():
    cloudformation = synthesized(
        SharedDomainExportsStack, "TestSharedDomainExportsStack"
    )
    assert cloudformation["Resources"] == {
        "DomainExportBridge": {
            "Type": "AWS::CloudFormation::WaitConditionHandle"
        }
    }
    outputs = cloudformation["Outputs"]
    for resource_id in ("AlpinePeak", "Portfolio", "MachineLearning"):
        assert outputs[f"{resource_id}HostedZoneId"] == {
            "Value": {
                "Fn::ImportValue": f"SharedOwned{resource_id}HostedZoneId"
            },
            "Export": {"Name": f"Shared{resource_id}HostedZoneId"},
        }
        assert outputs[f"{resource_id}CertificateArn"] == {
            "Value": {
                "Fn::ImportValue": f"SharedOwned{resource_id}CertificateArn"
            },
            "Export": {"Name": f"Shared{resource_id}CertificateArn"},
        }
