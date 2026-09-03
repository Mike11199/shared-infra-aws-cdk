"""Keep stable names that application stacks use to find domains and certificates.

The actual DNS zones and HTTPS certificates live in dedicated owner stacks. This
small compatibility layer republishes their identifiers (CloudFormation exports)
under the established names so application stacks do not depend on the split.
"""

from aws_cdk import CfnOutput, CfnResource, Fn, Stack
from constructs import Construct

from . import config


class SharedDomainExportsStack(Stack):
    """Keep existing export names while resource ownership moves to new stacks."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # CloudFormation requires at least one resource. This inert handle keeps
        # the existing SharedDomainsStack valid after its retained zones and
        # certificates move to their dedicated owner stacks.
        bridge_resource = CfnResource(
            self,
            "DomainExportBridgeResource",
            type="AWS::CloudFormation::WaitConditionHandle",
        )
        bridge_resource.override_logical_id("DomainExportBridge")

        for domain in config.DOMAIN_RESOURCES:
            resource_id = domain["id"]
            hosted_zone_value = Fn.import_value(
                f"SharedOwned{resource_id}HostedZoneId"
            )
            certificate_value = Fn.import_value(
                f"SharedOwned{resource_id}CertificateArn"
            )

            CfnOutput(
                self,
                f"{resource_id}HostedZoneId",
                value=hosted_zone_value,
                export_name=f"Shared{resource_id}HostedZoneId",
            )
            CfnOutput(
                self,
                f"{resource_id}CertificateArn",
                value=certificate_value,
                export_name=f"Shared{resource_id}CertificateArn",
            )
