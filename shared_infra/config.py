"""Physical identifiers and live properties used for one-time CDK import."""

AWS_ACCOUNT_ID = "456461478565"
AWS_REGION = "us-west-1"

VPC_ID = "vpc-031a34e2307900372"
PUBLIC_SUBNET_IDS = (
    "subnet-0069d564c7d9784e5",
    "subnet-0e28687dfd9d81afc",
)
ALB_SECURITY_GROUP_IDS = (
    "sg-003e2876012f4a06d",
    "sg-0190e299544ca1711",
)

LOAD_BALANCER_NAME = "consolidated-load-balancer"
LOAD_BALANCER_ARN = (
    "arn:aws:elasticloadbalancing:us-west-1:456461478565:loadbalancer/app/"
    "consolidated-load-balancer/cebd4e468e9c8526"
)
HTTP_LISTENER_ARN = (
    "arn:aws:elasticloadbalancing:us-west-1:456461478565:listener/app/"
    "consolidated-load-balancer/cebd4e468e9c8526/9ef98bdd931636ad"
)
HTTPS_LISTENER_ARN = (
    "arn:aws:elasticloadbalancing:us-west-1:456461478565:listener/app/"
    "consolidated-load-balancer/cebd4e468e9c8526/119a0202f44da309"
)

# Preserve the currently deployed default action exactly during import.
# These legacy target groups remain outside this shared stack.
DEFAULT_TARGET_GROUP_ARNS = (
    "arn:aws:elasticloadbalancing:us-west-1:456461478565:targetgroup/machine-learning-projects-2/093a0619190a10a9",
    "arn:aws:elasticloadbalancing:us-west-1:456461478565:targetgroup/michael-iwanek-portfolio-site-2/0dfa26d7d37f4cf4",
    "arn:aws:elasticloadbalancing:us-west-1:456461478565:targetgroup/react-ski-shop-2/374d0f142ed6d00f",
)

HOSTED_ZONE_COMMENT = "HostedZone created by Route53 Registrar"

DOMAIN_RESOURCES = (
    {
        "id": "AlpinePeak",
        "domain_name": "alpine-peak-climbing-ski-gear.com",
        "hosted_zone_id": "Z040844618MP488RZ84GN",
        "certificate_arn": (
            "arn:aws:acm:us-west-1:456461478565:certificate/"
            "98b115e8-c91b-4df3-b422-58cbcd420f30"
        ),
    },
    {
        "id": "Portfolio",
        "domain_name": "michael-iwanek-portfolio.com",
        "hosted_zone_id": "Z027864410Z1ZDQ87BDLV",
        "certificate_arn": (
            "arn:aws:acm:us-west-1:456461478565:certificate/"
            "b51e920e-bfeb-49f5-85a0-536b00972560"
        ),
    },
    {
        "id": "MachineLearning",
        "domain_name": "machine-learning-projects.com",
        "hosted_zone_id": "Z06957661TIDE98V5V9ZJ",
        "certificate_arn": (
            "arn:aws:acm:us-west-1:456461478565:certificate/"
            "91b663d1-8aff-4c52-b7c0-2a8c57cd7e76"
        ),
    },
)
