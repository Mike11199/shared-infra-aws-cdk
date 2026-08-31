"""Shared consolidated load balancer and listener ownership.

SharedInfrastructureStack owns the ALB and its HTTP/HTTPS listeners. It does
not own any website's root Route 53 A-alias record. Final ownership belongs in
each application stack because the alias is the application-specific route to
the shared ALB and shares the website lifecycle. Alpine Peak owns its alias
now; the live Portfolio and Machine Learning aliases remain unmanaged until
their separate application-CDK migration stages. SharedDomainsStack owns the
hosted zones and ACM certificates so a fresh environment has the one-way order
domains -> listener -> websites.
"""

from aws_cdk import CfnOutput, CfnTag, Fn, RemovalPolicy, Stack
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from constructs import Construct

from . import config


class SharedInfrastructureStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        load_balancer = elbv2.CfnLoadBalancer(
            self,
            "SharedAlbResource",
            name=config.LOAD_BALANCER_NAME,
            type="application",
            scheme="internet-facing",
            ip_address_type="ipv4",
            subnets=list(config.PUBLIC_SUBNET_IDS),
            security_groups=list(config.ALB_SECURITY_GROUP_IDS),
            tags=[
                CfnTag(
                    key="Description",
                    value=(
                        "Shared internet-facing HTTPS ALB for 3 domains. "
                        "Shared CDK owns the ALB and listeners. "
                        "Site CDKs own Route 53 DNS TLS certificates "
                        "host routing rules and target groups."
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

        # The listener requires one default certificate. SharedDomainsStack owns
        # the Alpine Peak certificate and exports its ARN, creating the intended
        # one-way domains -> listener dependency for a fresh environment.
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
