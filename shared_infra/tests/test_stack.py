from aws_cdk import App

from shared_infra import config
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


def test_exact_import_logical_ids():
    assert set(template()["Resources"]) == {
        "SharedAlb",
        "HttpListener",
        "HttpsListener",
    }


def test_alb_matches_active_physical_resource_and_is_retained():
    resource = template()["Resources"]["SharedAlb"]
    properties = resource["Properties"]

    assert properties["Name"] == "consolidated-load-balancer"
    assert properties["Scheme"] == "internet-facing"
    assert properties["Type"] == "application"
    assert properties["Subnets"] == list(config.PUBLIC_SUBNET_IDS)
    assert properties["SecurityGroups"] == list(config.ALB_SECURITY_GROUP_IDS)
    assert properties["Tags"] == [
        {
            "Key": "Description",
            "Value": (
                "Shared internet-facing HTTPS ALB for 3 domains. "
                "Shared CDK owns the ALB and listeners. "
                "Site CDKs own Route 53 DNS TLS certificates "
                "host routing rules and target groups."
            ),
        }
    ]
    assert resource["DeletionPolicy"] == "Retain"
    assert resource["UpdateReplacePolicy"] == "Retain"


def test_listeners_match_active_defaults_and_are_retained():
    cloudformation = template()
    http_resource = cloudformation["Resources"]["HttpListener"]
    https_resource = cloudformation["Resources"]["HttpsListener"]
    http = http_resource["Properties"]
    https = https_resource["Properties"]

    assert http["Port"] == 80
    assert http["Protocol"] == "HTTP"
    assert http["DefaultActions"][0]["RedirectConfig"] == {
        "Host": "#{host}",
        "Path": "/#{path}",
        "Port": "443",
        "Protocol": "HTTPS",
        "Query": "#{query}",
        "StatusCode": "HTTP_301",
    }

    assert https["Port"] == 443
    assert https["Protocol"] == "HTTPS"
    assert https["SslPolicy"] == "ELBSecurityPolicy-TLS13-1-2-2021-06"
    assert https["Certificates"] == [
        {
            "CertificateArn": {
                "Fn::ImportValue": "SharedAlpinePeakCertificateArn"
            }
        }
    ]

    assert https["DefaultActions"][0] == {
        "Type": "fixed-response",
        "FixedResponseConfig": {
            "StatusCode": "404",
            "ContentType": "text/plain",
            "MessageBody": "Not Found",
        },
    }

    for resource in (http_resource, https_resource):
        assert resource["DeletionPolicy"] == "Retain"
        assert resource["UpdateReplacePolicy"] == "Retain"


def test_stack_does_not_own_website_resources():
    cloudformation = template()
    assert resources(cloudformation, "AWS::Route53::HostedZone") == []
    assert resources(cloudformation, "AWS::Route53::RecordSet") == []
    assert resources(
        cloudformation, "AWS::CertificateManager::Certificate") == []
    assert resources(
        cloudformation, "AWS::ElasticLoadBalancingV2::ListenerRule") == []
    assert resources(
        cloudformation, "AWS::ElasticLoadBalancingV2::TargetGroup") == []
