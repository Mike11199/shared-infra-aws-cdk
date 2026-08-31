from aws_cdk import App

from shared_infra.domains_stack import SharedDomainsStack


def template() -> dict:
    app = App()
    stack = SharedDomainsStack(app, "TestSharedDomainsStack")
    return app.synth().get_stack_by_name(stack.stack_name).template


def test_stack_has_stable_logical_ids_for_three_zones_and_certificates():
    assert set(template()["Resources"]) == {
        "AlpinePeakHostedZone",
        "AlpinePeakCertificate",
        "PortfolioHostedZone",
        "PortfolioCertificate",
        "MachineLearningHostedZone",
        "MachineLearningCertificate",
    }


def test_domain_resources_match_live_properties_and_are_retained():
    cloudformation = template()

    expected = {
        "AlpinePeak": (
            "alpine-peak-climbing-ski-gear.com",
            "Z040844618MP488RZ84GN",
        ),
        "Portfolio": (
            "michael-iwanek-portfolio.com",
            "Z027864410Z1ZDQ87BDLV",
        ),
        "MachineLearning": (
            "machine-learning-projects.com",
            "Z06957661TIDE98V5V9ZJ",
        ),
    }

    for resource_id, (domain_name, hosted_zone_id) in expected.items():
        zone = cloudformation["Resources"][f"{resource_id}HostedZone"]
        certificate = cloudformation["Resources"][f"{resource_id}Certificate"]

        assert zone["Properties"] == {
            "Name": domain_name,
            "HostedZoneConfig": {
                "Comment": "HostedZone created by Route53 Registrar"
            },
        }
        assert certificate["Properties"] == {
            "DomainName": domain_name,
            "DomainValidationOptions": [
                {"DomainName": domain_name, "HostedZoneId": hosted_zone_id}
            ],
            "KeyAlgorithm": "RSA_2048",
            "ValidationMethod": "DNS",
            "CertificateTransparencyLoggingPreference": "ENABLED",
        }

        for resource in (zone, certificate):
            assert resource["DeletionPolicy"] == "Retain"
            assert resource["UpdateReplacePolicy"] == "Retain"


def test_stack_exports_hosted_zone_ids_and_certificate_arns():
    outputs = template()["Outputs"]

    for resource_id in ("AlpinePeak", "Portfolio", "MachineLearning"):
        assert outputs[f"{resource_id}HostedZoneId"] == {
            "Value": {"Ref": f"{resource_id}HostedZone"},
            "Export": {"Name": f"Shared{resource_id}HostedZoneId"},
        }
        assert outputs[f"{resource_id}CertificateArn"] == {
            "Value": {"Ref": f"{resource_id}Certificate"},
            "Export": {"Name": f"Shared{resource_id}CertificateArn"},
        }
