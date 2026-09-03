"""Own the HTTPS identity certificates for all three websites.

These certificates (ACM certificates) prove each site's identity to browsers.
AWS validates them through the domain address books (DNS hosted zones), then this
stack exports their identifiers for the shared HTTPS entry point to use.
"""

from aws_cdk import CfnOutput, Fn, RemovalPolicy, Stack
from aws_cdk import aws_certificatemanager as acm
from constructs import Construct

from . import config


class SharedCertificatesStack(Stack):
    """Own certificates after hosted zones exist and delegation is configured."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        for domain in config.DOMAIN_RESOURCES:
            resource_id = domain["id"]
            domain_name = domain["domain_name"]
            certificate = acm.CfnCertificate(
                self,
                f"{resource_id}CertificateResource",
                domain_name=domain_name,
                domain_validation_options=[
                    acm.CfnCertificate.DomainValidationOptionProperty(
                        domain_name=domain_name,
                        hosted_zone_id=Fn.import_value(
                            f"SharedOwned{resource_id}HostedZoneId"
                        ),
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
                f"{resource_id}CertificateArn",
                value=certificate.ref,
                export_name=f"SharedOwned{resource_id}CertificateArn",
            )
