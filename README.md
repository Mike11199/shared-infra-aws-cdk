# Shared AWS CDK Infrastructure

- This CDK deploys infrastructure shared by multiple websites in AWS.
- Because these resources are used by more than one site, no single website should own or recreate them.
- Each website CDK manages its own routing and application resources.

## Domain registration

- `SharedDomainsStack` does **not** register domain names.
- The three domain names were already registered manually in Route 53 Domains. The migration imported only their hosted zones and ACM certificates into CDK; it did not import the registrations.
- No registration or name-server action is required for the current environment.
- In a completely new account, register or transfer the domains manually, then point them to the hosted zones created or imported for that account.
- **Do not manually create the certificate CNAME.** ACM creates the validation CNAME automatically when the certificate stack is deployed.
- Do not copy a validation CNAME from an old certificate. Each new certificate can receive a different CNAME.

# Resources

- This repository manages:
  - Three Route 53 hosted zones
  - Three Certificate Manager (ACM) certificates
  - One consolidated Application Load Balancer (ALB)
  - HTTP and HTTPS listeners

```text
SharedDomainsStack
├── Alpine Peak hosted zone and certificate
├── Machine Learning hosted zone and certificate
└── Portfolio hosted zone and certificate

SharedInfrastructureStack
└── Consolidated Application Load Balancer
    ├── HTTP listener :80
    │   └── Redirects HTTP traffic to HTTPS
    └── HTTPS listener :443
        ├── Uses the Alpine Peak certificate by default
        ├── Accepts application rules from each website CDK
        └── Returns 404 when no website rule matches
```

- Hosted zones and certificates use `Retain` to protect them from accidental deletion.
- Registered domains, renewals, contacts, billing, and name-server delegation remain outside CDK.
- Route 53 creates the `NS` and `SOA` records for each hosted zone.
- Certificate-validation CNAME records are not manual resources.

## Website CDKs

- Website stacks own their application-specific resources:

```text
Website CDK
├── Root Route 53 A-alias
├── Host-header rule on the shared HTTPS listener
├── Target group
└── ECS application resources
```

- `AlpinePeakStack` currently owns its root A-alias and listener rule.
- The existing Portfolio and Machine Learning root A-aliases still need to be adopted by their website stacks.

## Deployment order

```text
SharedDomainsStack
-> SharedInfrastructureStack
-> Website stacks
```

- `SharedInfrastructureStack` consumes certificate outputs from `SharedDomainsStack`.
- Website stacks consume hosted-zone, load-balancer, and listener outputs from the shared stacks.

## Rebuilding in a new environment

- The current certificate definitions use production hosted-zone IDs.
- Before rebuilding in a new environment, separate hosted zones and certificates into ordered stacks and use `hosted_zone.ref`.
- Deploy hosted zones first, update the registered domains' name servers, and then deploy certificates.
- When the certificate stack is deployed, ACM automatically creates the validation CNAMEs in those hosted zones.

## File responsibilities

- `app.py` creates the shared domain and infrastructure stacks in dependency order.
- `shared_infra/domains_stack.py` defines hosted zones, certificates, retention policies, and exports.
- `shared_infra/stack.py` defines the shared load balancer, listeners, and exports.
- `shared_infra/config.py` contains the existing AWS resource identifiers and domain configuration.
- `shared_infra/tests/` verifies resource ownership, stable logical IDs, and listener behavior.
