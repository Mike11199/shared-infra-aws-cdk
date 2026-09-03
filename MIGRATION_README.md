# Shared infrastructure migration

## Status

Completed in AWS account `456461478565`, region `us-west-1`, on 2026-09-02/03.

- Existing VPC, subnets, internet gateway, route table, hosted zones, certificates, target groups, listener rules, and ECR repositories were retained and imported.
- The shared ALB now uses the dedicated `SharedAlbSecurityGroupId` security group.
- Portfolio and Machine Learning certificate attachments are owned by `SharedInfrastructureStack`.
- Application stacks consume shared CloudFormation exports; deployable CDK source contains no production resource IDs, account ID, or region literal.
- All eleven stacks report `IN_SYNC` with zero drifted resources.
- All shared and application CDK diffs report zero differences.
- All three HTTPS endpoints return `200`; HTTP redirects to HTTPS; all target groups are healthy.
- Generated migration artifacts, import maps, and migration-only entry points were deleted after final verification.

This file is the permanent audit record. Normal deployments use each repository's standard `app.py`; the one-time import procedure must not be repeated.

## Final ownership

```text
SharedNetworkStack
├── VPC, public subnets, internet gateway, and routing
└── shared ALB security group

SharedHostedZonesStack
└── three Route 53 hosted zones

SharedCertificatesStack
└── three ACM certificates

SharedDomainsStack
└── compatibility bridge for existing public domain exports

SharedInfrastructureStack
├── consolidated ALB
├── HTTP and HTTPS listeners
└── Portfolio and Machine Learning listener-certificate attachments

Application RepositoryStacks
└── retained ECR repositories

Application stacks
├── retained root A-alias
├── retained listener rule and target group
├── application security group
└── ECS application resources
```

Dependencies are one-way: shared stacks export values; application stacks import them.

## Migration record

The existing account was migrated in reviewed stages:

1. Captured a checksummed read-only inventory under `.migration/pre/`.
2. Imported the VPC, subnets, internet gateway, attachment, route table, and default route into `SharedNetworkStack`.
3. Added explicit subnet associations and the dedicated ALB security group.
4. Retained and released hosted zones and certificates from the old `SharedDomainsStack`.
5. Imported them into `SharedHostedZonesStack` and `SharedCertificatesStack` while preserving public export names through `SharedDomainsStack`.
6. Attached the new ALB security group alongside both legacy groups.
7. Imported all three existing ECR repositories.
8. Added retention policies to application target groups and listener rules.
9. Replaced their literal references with temporary parameter bridges, then retained, released, and re-imported the same physical resources using stable logical IDs and shared exports.
10. Updated each application ingress rule to trust the new ALB security group and verified service health.
11. Added the two existing non-default listener certificates as retained CloudFormation resources.
12. Removed the two legacy security groups from the ALB.
13. Captured `.migration/post/`, verified checksums, drift, endpoint health, target health, listener rules, certificates, DNS, ECR, and zero CDK diffs.

Every import proposal was import-only. Definite replacements were limited to normal template-only or stateless application changes; the ALB, listeners, hosted zones, certificates, target groups, listener rules, ECS services, network, and ECR repositories kept their physical identities.

## Fresh-account deployment

1. Bootstrap CDK in the target account and region.
2. Set `CDK_DEFAULT_ACCOUNT` and `CDK_DEFAULT_REGION` for shared deployments.
3. Deploy `SharedNetworkStack`.
4. Deploy `SharedHostedZonesStack`.
5. Update each registered domain to the new hosted-zone name servers.
6. Deploy `SharedCertificatesStack`; ACM creates validation records.
7. Deploy `SharedDomainsStack`.
8. Deploy `SharedInfrastructureStack`.
9. Deploy each application `RepositoryStack`.
10. Build and push application images.
11. Configure Alpine secrets, databases, and OAuth settings.
12. Deploy the three application stacks.

CDK does not register or transfer domains, populate secrets, create Alpine databases, or attach a security group to the existing RDS instance.

## Alpine RDS manual cutover

`AlpinePeakStack` exports `AlpinePeakRdsSecurityGroupId`. The new group allows PostgreSQL TCP `5432` only from the Alpine service security group.

1. Attach the new group to the existing RDS instance while keeping the current group.
2. Verify Alpine database access.
3. Remove the old broad group only after successful verification.
4. Reattach the old group immediately if connectivity fails.

This database change remains manual and was not performed by the migration.

## Safeguards

- Keep `.migration/` and import maps gitignored.
- Keep `Retain` policies on long-lived network, DNS, certificate, ALB, listener, routing, alias, and ECR resources.
- Never use migration-only apps for routine deployment.
- Review shared-infrastructure changes before deployment; unexpected deletion or replacement of retained production resources is a stop condition.
- Cross-stack exports are account-and-region local and cannot be removed while applications import them.
