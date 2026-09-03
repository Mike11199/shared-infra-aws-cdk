from aws_cdk import App

from shared_infra.stack import SharedInfrastructureStack


def template() -> dict:
    app = App()
    stack = SharedInfrastructureStack(app, "TestSharedInfrastructureStack")
    return app.synth().get_stack_by_name(stack.stack_name).template


def resources(cloudformation: dict, resource_type: str) -> list[dict]:
    return [
        resource
        for resource in cloudformation["Resources"].values()
        if resource["Type"] == resource_type
    ]


def test_exact_retained_edge_resources_and_certificate_attachments():
    cloudformation = template()
    assert set(cloudformation["Resources"]) == {
        "SharedAlb",
        "HttpListener",
        "HttpsListener",
        "PortfolioHttpsCertificateAttachment",
        "MachineLearningHttpsCertificateAttachment",
    }
    for logical_id in (
        "SharedAlb",
        "HttpListener",
        "HttpsListener",
        "PortfolioHttpsCertificateAttachment",
        "MachineLearningHttpsCertificateAttachment",
    ):
        resource = cloudformation["Resources"][logical_id]
        assert resource["DeletionPolicy"] == "Retain"
        assert resource["UpdateReplacePolicy"] == "Retain"


def test_alb_consumes_network_exports():
    properties = template()["Resources"]["SharedAlb"]["Properties"]
    assert properties["Subnets"] == [
        {"Fn::ImportValue": "SharedPublicSubnet1Id"},
        {"Fn::ImportValue": "SharedPublicSubnet2Id"},
    ]
    assert properties["SecurityGroups"] == [
        {"Fn::ImportValue": "SharedAlbSecurityGroupId"}
    ]


def test_https_listener_and_extra_certificates_use_certificate_exports():
    cloudformation = template()
    listener = cloudformation["Resources"]["HttpsListener"]["Properties"]
    assert listener["Certificates"] == [
        {"CertificateArn": {"Fn::ImportValue": "SharedAlpinePeakCertificateArn"}}
    ]
    assert listener["DefaultActions"][0]["FixedResponseConfig"]["StatusCode"] == "404"

    expected = {
        "PortfolioHttpsCertificateAttachment": "SharedPortfolioCertificateArn",
        "MachineLearningHttpsCertificateAttachment": (
            "SharedMachineLearningCertificateArn"
        ),
    }
    for logical_id, certificate_export in expected.items():
        extra = cloudformation["Resources"][logical_id]["Properties"]
        assert extra["ListenerArn"] == {"Ref": "HttpsListener"}
        assert extra["Certificates"] == [
            {"CertificateArn": {"Fn::ImportValue": certificate_export}}
        ]



def test_stack_does_not_own_website_or_network_resources():
    cloudformation = template()
    for resource_type in (
        "AWS::Route53::HostedZone",
        "AWS::Route53::RecordSet",
        "AWS::CertificateManager::Certificate",
        "AWS::ElasticLoadBalancingV2::ListenerRule",
        "AWS::ElasticLoadBalancingV2::TargetGroup",
        "AWS::EC2::VPC",
        "AWS::EC2::SecurityGroup",
    ):
        assert resources(cloudformation, resource_type) == []
