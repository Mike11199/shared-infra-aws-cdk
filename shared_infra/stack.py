"""Own the shared public web entry point used by all three websites.

This stack creates the shared load balancer (ALB), the connections accepting HTTP
and HTTPS traffic (listeners), and the extra certificate attachments. It does not
own each site's DNS alias, routing rule, or destination group; those belong to the
site's application stack. This boundary keeps the dependency order one-way:
network -> domains -> shared web entry point -> applications.
"""

from aws_cdk import CfnOutput, CfnTag, Fn, RemovalPolicy, Stack
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from constructs import Construct

from . import config


class SharedInfrastructureStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        load_balancer = elbv2.CfnLoadBalancer(
            self,
            "SharedAlbResource",
            name=config.LOAD_BALANCER_NAME,
            type="application",
            scheme="internet-facing",
            ip_address_type="ipv4",
            subnets=[
                Fn.import_value("SharedPublicSubnet1Id"),
                Fn.import_value("SharedPublicSubnet2Id"),
            ],
            security_groups=[Fn.import_value("SharedAlbSecurityGroupId")],
            tags=[
                CfnTag(
                    key="Description",
                    value=(
                        "Shared CDK owns the network ALB listeners and TLS "
                        "certificates. Site CDKs own DNS aliases host routing "
                        "rules target groups and application services."
                    ),
                )
            ],
            load_balancer_attributes=[
                elbv2.CfnLoadBalancer.LoadBalancerAttributeProperty(
                    key="deletion_protection.enabled", value="false"
                ),
                elbv2.CfnLoadBalancer.LoadBalancerAttributeProperty(
                    key="idle_timeout.timeout_seconds", value="60"
                ),
                elbv2.CfnLoadBalancer.LoadBalancerAttributeProperty(
                    key="routing.http2.enabled", value="true"
                ),
            ],
        )
        load_balancer.override_logical_id("SharedAlb")
        load_balancer.apply_removal_policy(RemovalPolicy.RETAIN)

        http_listener = elbv2.CfnListener(
            self,
            "HttpListenerResource",
            load_balancer_arn=load_balancer.ref,
            port=80,
            protocol="HTTP",
            default_actions=[
                elbv2.CfnListener.ActionProperty(
                    type="redirect",
                    order=1,
                    redirect_config=elbv2.CfnListener.RedirectConfigProperty(
                        protocol="HTTPS",
                        port="443",
                        host="#{host}",
                        path="/#{path}",
                        query="#{query}",
                        status_code="HTTP_301",
                    ),
                )
            ],
        )
        http_listener.override_logical_id("HttpListener")
        http_listener.apply_removal_policy(RemovalPolicy.RETAIN)

        # The listener requires one default certificate. SharedCertificatesStack
        # owns the Alpine Peak certificate and exports its ARN, creating the
        # intended one-way certificates -> listener dependency.
        https_listener = elbv2.CfnListener(
            self,
            "HttpsListenerResource",
            load_balancer_arn=load_balancer.ref,
            port=443,
            protocol="HTTPS",
            ssl_policy="ELBSecurityPolicy-TLS13-1-2-2021-06",
            certificates=[
                elbv2.CfnListener.CertificateProperty(
                    certificate_arn=Fn.import_value(
                        "SharedAlpinePeakCertificateArn"
                    )
                )
            ],
            # Fallback for HTTPS requests that do not match any website-owned
            # host-routing rule. Return 404 instead of sending unmatched traffic
            # to one of the application target groups.
            default_actions=[
                elbv2.CfnListener.ActionProperty(
                    type="fixed-response",
                    fixed_response_config=elbv2.CfnListener.FixedResponseConfigProperty(
                        status_code="404",
                        content_type="text/plain",
                        message_body="Not Found",
                    ),
                )
            ],
        )
        https_listener.override_logical_id("HttpsListener")
        https_listener.apply_removal_policy(RemovalPolicy.RETAIN)

        for resource_id in ("Portfolio", "MachineLearning"):
            attachment = elbv2.CfnListenerCertificate(
                self,
                f"{resource_id}HttpsCertificateAttachmentResource",
                listener_arn=https_listener.ref,
                certificates=[
                    elbv2.CfnListenerCertificate.CertificateProperty(
                        certificate_arn=Fn.import_value(
                            f"Shared{resource_id}CertificateArn"
                        )
                    )
                ],
            )
            attachment.override_logical_id(
                f"{resource_id}HttpsCertificateAttachment"
            )
            attachment.apply_removal_policy(RemovalPolicy.RETAIN)

        CfnOutput(
            self,
            "LoadBalancerArn",
            value=load_balancer.ref,
            export_name="SharedLoadBalancerArn",
        )
        CfnOutput(
            self,
            "LoadBalancerDnsName",
            value=load_balancer.attr_dns_name,
            export_name="SharedLoadBalancerDnsName",
        )
        CfnOutput(
            self,
            "LoadBalancerCanonicalHostedZoneId",
            value=load_balancer.attr_canonical_hosted_zone_id,
            export_name="SharedLoadBalancerCanonicalHostedZoneId",
        )
        CfnOutput(
            self,
            "HttpsListenerArn",
            value=https_listener.ref,
            export_name="SharedHttpsListenerArn",
        )
