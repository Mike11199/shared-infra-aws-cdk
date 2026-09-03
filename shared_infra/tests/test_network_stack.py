from aws_cdk import App

from shared_infra.network_stack import SharedNetworkStack


def template() -> dict:
    app = App()
    stack = SharedNetworkStack(app, "TestSharedNetworkStack")
    return app.synth().get_stack_by_name(stack.stack_name).template


def resources(cloudformation: dict, resource_type: str) -> list[dict]:
    return [
        resource
        for resource in cloudformation["Resources"].values()
        if resource["Type"] == resource_type
    ]


def test_network_stack_owns_complete_public_network():
    cloudformation = template()

    assert len(resources(cloudformation, "AWS::EC2::VPC")) == 1
    assert len(resources(cloudformation, "AWS::EC2::Subnet")) == 2
    assert len(resources(cloudformation, "AWS::EC2::InternetGateway")) == 1
    assert len(resources(cloudformation, "AWS::EC2::VPCGatewayAttachment")) == 1
    assert len(resources(cloudformation, "AWS::EC2::RouteTable")) == 1
    assert len(resources(cloudformation, "AWS::EC2::Route")) == 1
    assert len(resources(cloudformation, "AWS::EC2::SubnetRouteTableAssociation")) == 2

    vpc = resources(cloudformation, "AWS::EC2::VPC")[0]
    assert vpc["Properties"]["CidrBlock"] == "172.31.0.0/16"
    assert vpc["DeletionPolicy"] == "Retain"
    assert vpc["UpdateReplacePolicy"] == "Retain"

    subnets = resources(cloudformation, "AWS::EC2::Subnet")
    assert [subnet["Properties"]["CidrBlock"] for subnet in subnets] == [
        "172.31.0.0/20",
        "172.31.16.0/20",
    ]
    assert all(subnet["Properties"]["MapPublicIpOnLaunch"] for subnet in subnets)


def test_network_stack_owns_a_dedicated_alb_security_group():
    security_groups = resources(template(), "AWS::EC2::SecurityGroup")
    assert len(security_groups) == 1
    properties = security_groups[0]["Properties"]
    assert properties["GroupDescription"] == "Public HTTP and HTTPS access to the shared ALB"
    assert {rule["FromPort"] for rule in properties["SecurityGroupIngress"]} == {80, 443}


def test_network_stack_exports_generated_ids_and_availability_zones():
    outputs = template()["Outputs"]
    expected = {
        "VpcId": "SharedVpcId",
        "PublicSubnet1Id": "SharedPublicSubnet1Id",
        "PublicSubnet2Id": "SharedPublicSubnet2Id",
        "PublicSubnet1AvailabilityZone": "SharedPublicSubnet1AvailabilityZone",
        "PublicSubnet2AvailabilityZone": "SharedPublicSubnet2AvailabilityZone",
        "AlbSecurityGroupId": "SharedAlbSecurityGroupId",
    }
    for output_id, export_name in expected.items():
        assert outputs[output_id]["Export"]["Name"] == export_name

