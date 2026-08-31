"""Shared Route 53 hosted-zone and ACM certificate ownership.

SharedDomainsStack owns all hosted zones and certificates because they must
exist before the shared HTTPS listener can be created. It intentionally does
not own website root A-alias records. Those aliases belong in the application
stacks because they are website routing and should follow the website lifecycle
without transferring ownership of the long-lived zone. Alpine Peak owns its
alias now; Portfolio and Machine Learning will adopt their currently unmanaged
live aliases in their separate migration stages.
"""

from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_route53 as route53
from constructs import Construct

from . import config


class SharedDomainsStack(Stack):
    """Own the domain resources shared with the website stacks."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        for domain in config.DOMAIN_RESOURCES:
            resource_id = domain["id"]
            domain_name = domain["domain_name"]

            hosted_zone = route53.CfnHostedZone(
                self,
                f"{resource_id}HostedZoneResource",
                name=domain_name,
                hosted_zone_config=route53.CfnHostedZone.HostedZoneConfigProperty(
                    comment=config.HOSTED_ZONE_COMMENT
                ),
            )
            hosted_zone.override_logical_id(f"{resource_id}HostedZone")
            hosted_zone.apply_removal_policy(RemovalPolicy.RETAIN)

            certificate = acm.CfnCertificate(
                self,
                f"{resource_id}CertificateResource",
                domain_name=domain_name,
                domain_validation_options=[
                    acm.CfnCertificate.DomainValidationOptionProperty(
                        domain_name=domain_name,
                        hosted_zone_id=domain["hosted_zone_id"],
                    )
                ],
                key_algorithm="RSA_2048",
                validation_method="DNS",
                certificate_transparency_logging_preference="ENABLED",
            )
            certificate.override_logical_id(f"{resource_id}Certificate")
            certificate.apply_removal_policy(RemovalPolicy.RETAIN)

            CfnOutput(
                self,
                f"{resource_id}HostedZoneId",
                value=hosted_zone.ref,
                export_name=f"Shared{resource_id}HostedZoneId",
            )
            CfnOutput(
                self,
                f"{resource_id}CertificateArn",
                value=certificate.ref,
                export_name=f"Shared{resource_id}CertificateArn",
            )
