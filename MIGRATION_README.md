# Shared infrastructure migration

This migration makes the infrastructure reproducible in a new AWS account without copying production IDs. It replaces hidden dependencies on the current VPC, subnets, security groups, hosted-zone IDs, and manual certificate attachments with CDK-owned resources and stack outputs, while keeping dependencies one-way from shared infrastructure to each website.

## Problems solved

- New environments receive different AWS resource IDs.
- Certificate validation currently uses production hosted-zone IDs.
- Portfolio and Machine Learning certificate attachments are not managed by CloudFormation.
- Website stacks contain hard-coded network and listener IDs.
- The current ALB and RDS share broad manually managed security groups.
- ECR repositories and Alpine prerequisites have no single CDK owner.

## Replace hard-coded IDs with cross-stack references

The three website repositories currently copy production VPC, subnet, Availability Zone, ALB security-group, and listener IDs into `existing_resources.py`. Those values only work in the current account and become invalid when AWS creates different IDs in a fresh environment.

Use a CloudFormation cross-stack reference instead. The shared stack publishes the generated ID under a stable export name:

```python
CfnOutput(self, "VpcId", value=vpc.ref, export_name="SharedVpcId")
```

A website stack reads that export without knowing the physical ID:

```python
vpc_id = Fn.import_value("SharedVpcId")
```

Use the same pattern for `SharedPublicSubnet1Id`, `SharedPublicSubnet2Id`, their Availability Zones, `SharedAlbSecurityGroupId`, and `SharedHttpsListenerArn`. In the current account `SharedVpcId` resolves to the existing VPC; in a fresh account it resolves to the newly created VPC. The website source does not change.

## Desired final state

```text
SharedNetworkStack
  - VPC
  - public subnets and routing
  - ALB security group

SharedHostedZonesStack
  - three hosted zones

SharedCertificatesStack
  - three ACM certificates

SharedInfrastructureStack
  - shared ALB
  - HTTP and HTTPS listeners
  - all listener certificate attachments

Application repository stacks
  - application ECR repository

Application stacks
  - Route 53 A-alias
  - listener rule
  - target group
  - application security group
  - ECS application
```

## Dependency order

```text
SharedNetworkStack
SharedHostedZonesStack
  -> SharedCertificatesStack
  -> SharedInfrastructureStack
  -> application stacks
```

Shared stacks never import application outputs. Application stacks may deploy independently after shared infrastructure is ready.

## Safe migration order

1. Inventory the live network, domains, certificates, ALB, listeners, and certificate attachments.
2. Model the network exactly and import existing resources into `SharedNetworkStack` with `Retain` policies.
3. Export the VPC, subnet, and ALB security-group IDs.
4. Separate hosted zones and certificates without replacing either.
5. Keep hosted-zone exports stable; use temporary certificate exports if ownership must move between stacks.
6. Manage the Portfolio and Machine Learning listener certificate attachments in `SharedInfrastructureStack`.
7. Create dedicated ALB, application, and RDS security groups.
8. Migrate Alpine Peak, Portfolio, and Machine Learning one repository at a time to shared outputs.
9. Move each ECR repository into an application repository stack.
10. Remove hard-coded production IDs only after every consumer has migrated.
11. Verify HTTPS, target health, CloudFormation drift, and zero unexpected CDK diff after each stage.

Reject any change set that unexpectedly deletes or replaces a hosted zone, certificate, ALB, listener, listener rule, target group, or application service.

## Fresh-environment deployment

1. Bootstrap CDK in the target account and region.
2. Deploy `SharedNetworkStack`.
3. Deploy `SharedHostedZonesStack`.
4. Update each registered domain's name servers manually.
5. Deploy `SharedCertificatesStack`; ACM creates validation CNAMEs automatically.
6. Deploy `SharedInfrastructureStack`.
7. Deploy each application repository stack and push images.
8. Populate Alpine secrets and configure its databases and OAuth settings.
9. Deploy the three application stacks.

## Manual steps

- Register or transfer the domain names and update their name servers.
- Configure GitHub AWS authentication and bootstrap CDK.
- Populate secret values; never store them in CDK source.
- Do not manually create ACM validation CNAMEs.

## ECR bootstrap

Each application should own its ECR repository in a small `RepositoryStack`. This removes the image chicken-and-egg problem while keeping ECR under CloudFormation ownership.

Each GitHub Actions pipeline runs:

```text
tests
-> deploy RepositoryStack
-> build and push images
-> deploy ApplicationStack
-> health check
```

The repository deployment is intentionally repeated. It creates ECR on the first or fresh-environment run and is a no-op when unchanged. Existing repositories must be imported once so their images are preserved; then remove the workflow's manual `describe-or-create` logic.

The dependency remains one-way: `ApplicationStack -> RepositoryStack`. The repository stack never references the application stack.

## Current AWS state

### CDK-managed

- Shared CDK: three hosted zones, three ACM certificates, shared ALB, and HTTP/HTTPS listeners.
- Application CDKs: three A-alias records, listener rules, target groups, ECS services, and application capacity.
- All three active target groups are attached and managed. No old target groups remain.

### Active but unmanaged

- Default VPC, public subnets, internet routing, and current ALB security groups.
- Portfolio and Machine Learning listener certificate attachments.
- Three active ECR repositories created by GitHub Actions rather than owned by CloudFormation.
- Alpine execution role, log groups, SSM parameters, RDS database, MongoDB, and OAuth configuration.
- Registered domains and name-server delegation.

### Problems

- Physical network and listener IDs are copied into application repositories.
- Certificate validation uses production hosted-zone IDs, so fresh zones receive the wrong references.
- Portfolio and Machine Learning HTTPS certificate attachments cannot be recreated from the current templates.
- The ALB and public RDS database use broad manually managed security groups.
- Two stopped legacy EC2 instances, their EBS volumes, and Elastic IPs remain outside CDK and require a separate keep-or-delete decision.

## Certificates and HTTPS

All three certificates are already managed by CDK. However, attaching a certificate to the load balancer's HTTPS listener is a separate resource:

- Alpine's certificate attachment is managed by CDK.
- Portfolio's certificate attachment was created manually.
- Machine Learning's certificate attachment was created manually.

The migration brings the two manual attachments under `SharedInfrastructureStack` without detaching or recreating the certificates. In a fresh account, CDK creates all three certificates and attaches all three to the listener.

Moving the certificates from `SharedDomainsStack` to the proposed `SharedCertificatesStack` is a separate ownership move. Retain and import the existing certificates so their ARNs do not change.

## Migration safeguards

- Existing account: adopt live resources with temporary import mappings; never commit physical IDs. Fresh account: deploy normally and let AWS generate new IDs.
- Keep `Retain` policies, disable the affected workflow, review no-execute change sets, and reject unexpected replacements or deletions.
- Changing Portfolio or Machine Learning from a literal listener ARN to `SharedHttpsListenerArn` may replace the listener rule; migrate each rule with retain/release/import instead.
- Network ownership includes the internet gateway, public route table, default route, and subnet associations—not only the VPC and subnets.
- Create and verify dedicated ALB, application, and RDS security groups before removing broad existing access.
- Import existing ECR repositories with their images, use `Retain`, and pass immutable image tags or digests to application deployments.
- Cross-stack exports are account-and-region local, must remain uniquely named, and cannot be removed while applications import them.
- Remove hard-coded account and region values along with physical resource IDs.
