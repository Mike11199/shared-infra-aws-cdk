# Production Resource Migration

This file records how existing AWS resources were adopted without recreating them or interrupting the websites. Do not rerun these steps against the current production account.

## Migration paths

### Import an unmanaged resource

The ECR repositories and shared network existed in AWS but were not owned by another CloudFormation stack.

```text
define the existing resource in the new CDK stack
-> create and review an import change set
-> execute the import
-> verify the physical resource ID and stack drift
```

### Move a resource between stacks

CloudFormation cannot transfer a resource directly between stacks, and `cdk import` rejects a resource while another stack owns it.

```text
add Retain to the resource in the old stack
-> deploy the Retain policy
-> deploy a temporary old-stack template without the resource
-> old stack releases ownership while the real resource stays running
-> define the same resource in the new stack
-> create, review, and execute the import change set
-> verify the physical resource ID and stack drift
```

Removing a resource from a deployed template normally tells CloudFormation to delete it. `Retain` prevented deletion during the short period between release from the old stack and import into the new stack.

For example, the hosted zones were removed from the temporary `SharedDomainsStack` template. CloudFormation stopped listing them in that stack but left the real Route 53 hosted zones running. `cdk import` then attached them to `SharedHostedZonesStack`.

## Import example

These commands imported the existing `portfolio-website` ECR repository into `PortfolioRepositoryStack`. They are a historical example only.

1. Create the import change set without executing it:

```bash
cdk import PortfolioRepositoryStack \
  --resource-mapping-inline \
  '{"PortfolioRepository":{"RepositoryName":"portfolio-website"}}' \
  --change-set-name import-portfolio-repository \
  --no-execute \
  --profile michael-projects
```

2. Inspect the change set:

```bash
aws cloudformation describe-change-set \
  --stack-name PortfolioRepositoryStack \
  --change-set-name import-portfolio-repository \
  --profile michael-projects
```

3. Execute the reviewed change set:

```bash
aws cloudformation execute-change-set \
  --stack-name PortfolioRepositoryStack \
  --change-set-name import-portfolio-repository \
  --profile michael-projects
```

4. Wait for the import:

```bash
aws cloudformation wait stack-import-complete \
  --stack-name PortfolioRepositoryStack \
  --profile michael-projects
```

5. Confirm that CDK matches AWS:

```bash
cdk diff PortfolioRepositoryStack \
  --change-set=false \
  --profile michael-projects
```

`--no-execute` created only a reviewable change set. Executing it assigned CloudFormation ownership of the existing repository without recreating it or deleting its images.

## Safeguards and verification

- Every migration change set was reviewed before execution.
- Existing physical resource IDs were checked after import.
- Production endpoints remained healthy during the migration.
- All eleven stacks matched the CDK templates and reported no drift when migration finished.
- Migration-only programs and resource maps were deleted.
- `Retain` remains on production resources whose accidental deletion could cause data loss or an outage.
- Stop and investigate if a future `cdk diff` proposes deleting or replacing a production resource.
