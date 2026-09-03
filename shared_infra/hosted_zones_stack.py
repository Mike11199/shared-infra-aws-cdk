"""Own the internet address books for all three websites.

These address books (Route 53 hosted zones) connect each domain name to AWS.
They are separate from certificates and applications so a website can be rebuilt
without replacing its domain registration records or reversing stack dependencies.
"""

from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_route53 as route53
from constructs import Construct

from . import config


class SharedHostedZonesStack(Stack):
    """Own hosted zones without depending on certificates or applications."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        for domain in config.DOMAIN_RESOURCES:
            resource_id = domain["id"]
            hosted_zone = route53.CfnHostedZone(
                self,
                f"{resource_id}HostedZoneResource",
                name=domain["domain_name"],
                hosted_zone_config=route53.CfnHostedZone.HostedZoneConfigProperty(
                    comment=config.HOSTED_ZONE_COMMENT
                ),
            )
            hosted_zone.override_logical_id(f"{resource_id}HostedZone")
            hosted_zone.apply_removal_policy(RemovalPolicy.RETAIN)

            CfnOutput(
                self,
                f"{resource_id}HostedZoneId",
                value=hosted_zone.ref,
                export_name=f"SharedOwned{resource_id}HostedZoneId",
            )
