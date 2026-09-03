"""Build the five shared stacks in a safe one-way order.

The order is network -> domain address books -> HTTPS certificates -> stable
export names -> shared web entry point. It lets a fresh AWS account deploy from
scratch without copied resource identifiers or stacks that depend on each other.
"""

import os

from aws_cdk import App, Environment

from shared_infra.certificates_stack import SharedCertificatesStack
from shared_infra.domain_exports_stack import SharedDomainExportsStack
from shared_infra.hosted_zones_stack import SharedHostedZonesStack
from shared_infra.network_stack import SharedNetworkStack
from shared_infra.stack import SharedInfrastructureStack


app = App()
env = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION"),
)
network_stack = SharedNetworkStack(
    app, "SharedNetworkStack", env=env, analytics_reporting=False
)
hosted_zones_stack = SharedHostedZonesStack(
    app, "SharedHostedZonesStack", env=env, analytics_reporting=False
)
certificates_stack = SharedCertificatesStack(
    app, "SharedCertificatesStack", env=env, analytics_reporting=False
)
certificates_stack.add_stack_dependency(hosted_zones_stack)
domain_exports_stack = SharedDomainExportsStack(
    app, "SharedDomainsStack", env=env, analytics_reporting=False
)
domain_exports_stack.add_stack_dependency(certificates_stack)
infrastructure_stack = SharedInfrastructureStack(
    app, "SharedInfrastructureStack", env=env
)
infrastructure_stack.add_stack_dependency(network_stack)
infrastructure_stack.add_stack_dependency(domain_exports_stack)
app.synth()
