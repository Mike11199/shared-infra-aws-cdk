from aws_cdk import App, Environment

from shared_infra.config import AWS_ACCOUNT_ID, AWS_REGION
from shared_infra.domains_stack import SharedDomainsStack
from shared_infra.stack import SharedInfrastructureStack


app = App()
environment = Environment(account=AWS_ACCOUNT_ID, region=AWS_REGION)
domains_stack = SharedDomainsStack(
    app,
    "SharedDomainsStack",
    env=environment,
    analytics_reporting=False,
)
infrastructure_stack = SharedInfrastructureStack(
    app,
    "SharedInfrastructureStack",
    env=environment,
)
infrastructure_stack.add_stack_dependency(domains_stack)
app.synth()
