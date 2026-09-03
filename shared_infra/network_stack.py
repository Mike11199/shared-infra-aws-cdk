"""Own the shared private network and its controlled connection to the internet.

This stack creates the isolated AWS network (VPC), two internet-facing sections
(public subnets), the path that carries internet traffic (public routing), and
the firewall rules for the shared web entry point (ALB security group). Keeping
these foundations separate lets every other stack depend on them in one direction.
"""

from aws_cdk import CfnOutput, Fn, RemovalPolicy, Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from . import config


class SharedNetworkStack(Stack):
    """Own the network resources consumed by the shared edge and applications."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.CfnVPC(
            self,
            "VpcResource",
            cidr_block=config.VPC_CIDR,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            instance_tenancy="default",
        )
        vpc.override_logical_id("Vpc")
        vpc.apply_removal_policy(RemovalPolicy.RETAIN)

        internet_gateway = ec2.CfnInternetGateway(self, "InternetGatewayResource")
        internet_gateway.override_logical_id("InternetGateway")
        internet_gateway.apply_removal_policy(RemovalPolicy.RETAIN)

        gateway_attachment = ec2.CfnVPCGatewayAttachment(
            self,
            "InternetGatewayAttachmentResource",
            vpc_id=vpc.ref,
            internet_gateway_id=internet_gateway.ref,
        )
        gateway_attachment.override_logical_id("InternetGatewayAttachment")
        gateway_attachment.apply_removal_policy(RemovalPolicy.RETAIN)

        route_table = ec2.CfnRouteTable(
            self, "PublicRouteTableResource", vpc_id=vpc.ref
        )
        route_table.override_logical_id("PublicRouteTable")
        route_table.apply_removal_policy(RemovalPolicy.RETAIN)

        default_route = ec2.CfnRoute(
            self,
            "PublicDefaultRouteResource",
            route_table_id=route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=internet_gateway.ref,
        )
        default_route.override_logical_id("PublicDefaultRoute")
        default_route.add_resource_dependency(gateway_attachment)
        default_route.apply_removal_policy(RemovalPolicy.RETAIN)

        subnets: list[ec2.CfnSubnet] = []
        for index, cidr in enumerate(config.PUBLIC_SUBNET_CIDRS):
            number = index + 1
            subnet = ec2.CfnSubnet(
                self,
                f"PublicSubnet{number}Resource",
                vpc_id=vpc.ref,
                cidr_block=cidr,
                availability_zone=Fn.select(index, Fn.get_azs()),
                map_public_ip_on_launch=True,
            )
            subnet.override_logical_id(f"PublicSubnet{number}")
            subnet.apply_removal_policy(RemovalPolicy.RETAIN)
            subnets.append(subnet)

            association = ec2.CfnSubnetRouteTableAssociation(
                self,
                f"PublicSubnet{number}RouteTableAssociationResource",
                subnet_id=subnet.ref,
                route_table_id=route_table.ref,
            )
            association.override_logical_id(
                f"PublicSubnet{number}RouteTableAssociation"
            )
            association.apply_removal_policy(RemovalPolicy.RETAIN)

        alb_security_group = ec2.CfnSecurityGroup(
            self,
            "AlbSecurityGroupResource",
            group_description="Public HTTP and HTTPS access to the shared ALB",
            vpc_id=vpc.ref,
            security_group_ingress=[
                ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="tcp",
                    from_port=80,
                    to_port=80,
                    cidr_ip="0.0.0.0/0",
                    description="Public HTTP redirected to HTTPS",
                ),
                ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="tcp",
                    from_port=443,
                    to_port=443,
                    cidr_ip="0.0.0.0/0",
                    description="Public HTTPS",
                ),
            ],
        )
        alb_security_group.override_logical_id("AlbSecurityGroup")
        alb_security_group.apply_removal_policy(RemovalPolicy.RETAIN)

        CfnOutput(self, "VpcId", value=vpc.ref, export_name="SharedVpcId")
        for index, subnet in enumerate(subnets, start=1):
            CfnOutput(
                self,
                f"PublicSubnet{index}Id",
                value=subnet.ref,
                export_name=f"SharedPublicSubnet{index}Id",
            )
            CfnOutput(
                self,
                f"PublicSubnet{index}AvailabilityZone",
                value=subnet.attr_availability_zone,
                export_name=f"SharedPublicSubnet{index}AvailabilityZone",
            )
        CfnOutput(
            self,
            "AlbSecurityGroupId",
            value=alb_security_group.attr_group_id,
            export_name="SharedAlbSecurityGroupId",
        )
