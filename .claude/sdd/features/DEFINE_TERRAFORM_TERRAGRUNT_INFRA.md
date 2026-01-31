# DEFINE: Terraform + Terragrunt Infrastructure

> Build production IaC infrastructure for the invoice processing pipeline with reusable Terraform modules and Terragrunt configuration for the production environment.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | TERRAFORM_TERRAGRUNT_INFRA |
| **Date** | 2026-01-30 |
| **Author** | define-agent |
| **Status** | Ready for Design |
| **Clarity Score** | 15/15 |

---

## Problem Statement

The invoice processing pipeline requires consistent, repeatable infrastructure deployment for the production environment. Manual infrastructure setup is error-prone and creates configuration drift. Without IaC, the team cannot reliably deploy, scale, or recover the production pipeline for the April 1, 2026 launch.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Pedro Lima | Platform/DevOps Lead | Needs reproducible production infrastructure that can be versioned and reviewed |
| João Silva | Senior Data Engineer | Needs reliable production deployment for invoice processing |
| Ana Costa | ML Engineer | Needs production environment for Gemini extraction at scale |
| Future Team Members | Engineers | Need self-documenting infrastructure that's easy to understand |

---

## Goals

What success looks like (prioritized):

| Priority | Goal |
|----------|------|
| **MUST** | Create 6 reusable Terraform modules (cloud-run, pubsub, gcs, bigquery, iam, secrets) |
| **MUST** | Configure Terragrunt for production environment deployment |
| **MUST** | Deploy all 4 Cloud Run functions to production via IaC |
| **MUST** | Create all supporting GCP resources (Pub/Sub, GCS, BigQuery, IAM) in production |
| **SHOULD** | Implement GCS backend for Terraform state with versioning |
| **SHOULD** | Document module inputs/outputs and usage examples |
| **COULD** | Add validation rules to Terraform variables |
| **COULD** | Create CI/CD integration for `terraform validate` and `terragrunt plan` |

---

## Success Criteria

Measurable outcomes:

- [ ] All 6 Terraform modules pass `terraform validate`
- [ ] `terragrunt run-all apply` deploys complete production environment successfully
- [ ] All 4 Cloud Run functions healthy and responding in production
- [ ] Production scaling values applied correctly (min_instances, max_instances)
- [ ] Module dependencies resolve correctly (iam → gcs → cloud-run order)
- [ ] State files stored in GCS with versioning enabled
- [ ] Terraform plan shows no changes after initial apply (idempotent)

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Production environment deploy | Empty prod GCP project | `terragrunt run-all apply` in environments/prod | All resources created, Cloud Run functions healthy |
| AT-002 | Production scaling | Functions deployed | Check Cloud Run configuration | min_instances=1-2, max_instances=50-100 per function |
| AT-003 | Module idempotency | Resources already exist | Run `terragrunt apply` again | Plan shows 0 changes |
| AT-004 | Dependency ordering | Clean environment | Deploy cloud-run before iam | Terragrunt fails with clear error about dependency |
| AT-005 | State backend | Any module deployment | Check state location | State in GCS bucket `eda-gemini-prd-tfstate` |
| AT-006 | Resource naming | Production deployed | Check resource names | All resources have `-prd` suffix |
| AT-007 | Secret access | Cloud Run function deployed | Function starts | Can access secrets from Secret Manager |
| AT-008 | Compliance retention | Archive bucket created | Check lifecycle policy | 7-year retention configured |

---

## Out of Scope

Explicitly NOT included in this feature:

- **Development environment** - Dev uses gcloud CLI for rapid iteration (per meeting decision)
- **CI/CD pipeline** - GitHub Actions workflow is a separate feature
- **Monitoring dashboards** - Cloud Monitoring configuration is P2
- **Multi-region deployment** - Single region (us-central1) for MVP
- **Custom domain configuration** - Cloud Run default URLs sufficient
- **VPC configuration** - Using default VPC, private networking is future work
- **Cost optimization policies** - Committed use discounts, budget alerts are future
- **Disaster recovery automation** - Manual recovery acceptable for MVP

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Technical | Must use Terraform >= 1.5 with Google provider >= 5.0 | Modules must use current HCL syntax |
| Technical | Terragrunt >= 0.55 required | Can use latest features like `run-all` |
| Technical | GCP project `eda-gemini-prd` already created | Module creates resources within project |
| Timeline | Production launch: April 1, 2026 | Infrastructure must be complete by Feb 28 |
| Resource | Pedro Lima sole DevOps resource | Limited review bandwidth |
| Compliance | 7-year retention for prod archive bucket | Lifecycle rules must respect compliance |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `infra/` at repository root | Follows design document structure |
| **KB Domains** | terraform, terragrunt, gcp | Patterns from `.claude/kb/` |
| **IaC Impact** | This IS the IaC feature | Creates all Terraform/Terragrunt files |

**Directory Structure:**

```
infra/
├── terragrunt.hcl                    # Root configuration
├── modules/                          # Reusable Terraform modules
│   ├── cloud-run/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   ├── pubsub/
│   ├── gcs/
│   ├── bigquery/
│   ├── iam/
│   └── secrets/
└── environments/
    └── prod/
        ├── env.hcl                   # Production variables
        ├── gcs/terragrunt.hcl
        ├── pubsub/terragrunt.hcl
        ├── bigquery/terragrunt.hcl
        ├── iam/terragrunt.hcl
        ├── secrets/terragrunt.hcl
        └── cloud-run/terragrunt.hcl
```

**Note:** Dev environment intentionally excluded. Modules are reusable—dev can be added later by creating `environments/dev/` with different `env.hcl` values.

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | GCP project `eda-gemini-prd` exists | Would need to create project first | [ ] |
| A-002 | Terraform state bucket `eda-gemini-prd-tfstate` can be created manually | Would need bootstrap process | [ ] |
| A-003 | Container images already built and in GCR | Cloud Run module needs image URLs | [ ] |
| A-004 | API keys for Gemini, OpenRouter, LangFuse available | Secrets module needs initial values | [ ] |
| A-005 | GCP APIs enabled (Cloud Run, Pub/Sub, BigQuery, etc.) | Would need API enablement in Terraform | [ ] |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Clear need for reproducible production IaC |
| Users | 3 | DevOps lead, data engineers, ML engineer identified |
| Goals | 3 | 6 specific modules with clear deliverables |
| Success | 3 | Measurable: modules validate, production deploys |
| Scope | 3 | Explicit directory structure, dev explicitly excluded |
| **Total** | **15/15** | |

---

## Open Questions

None - ready for Design.

All requirements are captured from:
- Design document: `design/infra-terraform-terragrunt-design.md`
- Meeting decisions: `notes/05-devops-infrastructure.md`

---

## References

| Document | Purpose |
|----------|---------|
| [design/infra-terraform-terragrunt-design.md](../../../design/infra-terraform-terragrunt-design.md) | Detailed infrastructure design |
| [notes/05-devops-infrastructure.md](../../../notes/05-devops-infrastructure.md) | Meeting decisions and approvals |
| [.claude/kb/terraform/](../../kb/terraform/) | Terraform patterns |
| [.claude/kb/terragrunt/](../../kb/terragrunt/) | Terragrunt patterns |

---

## Revision History

| Version | Date       | Author        | Changes                                                      |
|---------|------------|---------------|--------------------------------------------------------------|
| 1.0     | 2026-01-30 | define-agent  | Initial version with dev + prod environments                 |
| 1.1     | 2026-01-30 | iterate-agent | Scope reduced to production only; dev moved to out-of-scope  |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_TERRAFORM_TERRAGRUNT_INFRA.md`
