"""Environment-independent configuration for shared infrastructure."""

VPC_CIDR = "172.31.0.0/16"
PUBLIC_SUBNET_CIDRS = ("172.31.0.0/20", "172.31.16.0/20")

LOAD_BALANCER_NAME = "consolidated-load-balancer"
HOSTED_ZONE_COMMENT = "HostedZone created by Route53 Registrar"

DOMAIN_RESOURCES = (
    {
        "id": "AlpinePeak",
        "domain_name": "alpine-peak-climbing-ski-gear.com",
    },
    {
        "id": "Portfolio",
        "domain_name": "michael-iwanek-portfolio.com",
    },
    {
        "id": "MachineLearning",
        "domain_name": "machine-learning-projects.com",
    },
)
