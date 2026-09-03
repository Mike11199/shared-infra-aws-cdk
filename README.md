# Shared AWS CDK infrastructure

Shared network, domain, certificate, and load-balancer infrastructure for three websites.

## Ownership

```text
SharedNetworkStack
├── VPC
├── two public subnets
├── internet gateway and public routing
└── dedicated ALB security group

SharedHostedZonesStack
└── Alpine Peak, Portfolio, and Machine Learning hosted zones

SharedCertificatesStack
└── one ACM certificate for each hosted zone

SharedDomainsStack (compatibility export bridge; no domain resources)
└── preserves the existing public hosted-zone and certificate export names

SharedInfrastructureStack
└── consolidated ALB
    ├── HTTP-to-HTTPS listener
    ├── HTTPS listener
    └── all three certificate attachments
```

Application repositories own their own:

- ECR `RepositoryStack`
- Route 53 root A-alias
- listener rule and target group
- application security group
- ECS application resources

Alpine Peak also defines a dedicated retained RDS security group. The database remains manually configured; attaching the new group and removing the old broad group are separate operator actions.

## Exports

- Network: `SharedVpcId`, two public-subnet IDs and Availability Zones, and `SharedAlbSecurityGroupId`
- Domains: dedicated owner stacks publish internal `SharedOwned<Site>...` values; the compatibility `SharedDomainsStack` re-exports the existing public `Shared<Site>HostedZoneId` and `Shared<Site>CertificateArn` names
- Load balancer: ARN, DNS name, canonical hosted-zone ID, and `SharedHttpsListenerArn`

Applications import these names. They do not contain production VPC, subnet, security-group, listener, account, or region IDs.

## Deployment order

```text
SharedNetworkStack
SharedHostedZonesStack
  -> SharedCertificatesStack
  -> SharedDomainsStack export bridge
SharedNetworkStack + SharedDomainsStack export bridge
  -> SharedInfrastructureStack
  -> application RepositoryStacks
  -> image pushes
  -> application stacks
```

The order above applies to new environments and routine deployments. The current account completed the retained-resource migration recorded in [MIGRATION_README.md](MIGRATION_README.md).

## Domain registration

- CDK does not register or transfer domains.
- In a new account, update each registered domain to the name servers created by its hosted zone.
- ACM creates validation CNAMEs automatically after hosted-zone delegation is correct.
- Never copy validation CNAMEs from an old certificate.

## Deployment safeguards

- The migration completed with all eleven stacks `IN_SYNC` and zero final CDK differences.
- Hosted zones, certificates, imported network resources, the ALB, listeners, certificate attachments, ECR repositories, DNS aliases, listener rules, target groups, and the Alpine RDS security group use `Retain` where loss would be unsafe.
- Use normal `app.py` deployments. One-time migration programs and physical-resource maps were removed after verification.
- Reject unexpected deletion or replacement of retained production resources.

## Files

- `app.py` creates the owner stacks, compatibility export bridge, and one-way dependencies.
- `shared_infra/domain_exports_stack.py` keeps those public export names stable after ownership moves.
- `shared_infra/network_stack.py` owns shared networking and the ALB security group.
- `shared_infra/hosted_zones_stack.py` owns hosted zones.
- `shared_infra/certificates_stack.py` owns certificates and consumes hosted-zone exports.
- `shared_infra/stack.py` owns the ALB, listeners, and certificate attachments.
- `shared_infra/config.py` contains portable names and CIDR ranges only.
- `shared_infra/tests/` verifies ownership, retention, exports, and dependencies.
