# DESIGN: Terraform + Terragrunt Infrastructure

> Technical design for production IaC infrastructure with 6 reusable Terraform modules and Terragrunt orchestration

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | TERRAFORM_TERRAGRUNT_INFRA |
| **Date** | 2026-01-30 |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_TERRAFORM_TERRAGRUNT_INFRA.md](./DEFINE_TERRAFORM_TERRAGRUNT_INFRA.md) |
| **Status** | Ready for Build |

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    TERRAFORM + TERRAGRUNT ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  infra/                                                                          │
│  ├─ terragrunt.hcl ◄─────────────────────────────────────────────────────────┐  │
│  │   (Root Config: backend, provider generation)                              │  │
│  │                                                                            │  │
│  ├─ modules/                         ├─ environments/                         │  │
│  │  ┌────────────┐                   │  └─ prod/                              │  │
│  │  │  secrets   │ ◄─────────────────│─────├─ env.hcl (prod variables)        │  │
│  │  └─────┬──────┘                   │     ├─ secrets/terragrunt.hcl ─────────┘  │
│  │        │                          │     ├─ iam/terragrunt.hcl                 │
│  │  ┌─────▼──────┐                   │     ├─ gcs/terragrunt.hcl                 │
│  │  │    iam     │ ◄─────────────────│     ├─ pubsub/terragrunt.hcl              │
│  │  └─────┬──────┘                   │     ├─ bigquery/terragrunt.hcl            │
│  │        │                          │     └─ cloud-run/terragrunt.hcl           │
│  │  ┌─────┴─────┬──────────┐         │                                           │
│  │  ▼           ▼          ▼         │                                           │
│  │ ┌────┐    ┌────────┐  ┌─────────┐ │                                           │
│  │ │gcs │    │pubsub  │  │bigquery │ │                                           │
│  │ └──┬─┘    └───┬────┘  └────┬────┘ │                                           │
│  │    │          │            │      │                                           │
│  │    └──────────┼────────────┘      │                                           │
│  │               ▼                   │                                           │
│  │        ┌───────────┐              │                                           │
│  │        │ cloud-run │              │                                           │
│  │        └───────────┘              │                                           │
│  │                                   │                                           │
│  └───────────────────────────────────┘                                           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           GCP PRODUCTION ENVIRONMENT                             │
│                              (eda-gemini-prd)                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                           Secret Manager                                  │   │
│  │  eda-gemini-prd-gemini-api-key | eda-gemini-prd-openrouter-api-key       │   │
│  │  eda-gemini-prd-langfuse-secret                                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                           Service Accounts                                │   │
│  │  sa-tiff-converter-prd | sa-classifier-prd | sa-extractor-prd            │   │
│  │  sa-bq-writer-prd | sa-pubsub-invoker-prd                                │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │      GCS        │  │     Pub/Sub     │  │    BigQuery     │                  │
│  │  4 buckets      │  │  5 topics       │  │  1 dataset      │                  │
│  │  + lifecycle    │  │  + DLQ          │  │  4 tables       │                  │
│  │  + notification │  │  + subscriptions│  │  + partitioning │                  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                           Cloud Run Services                              │   │
│  │  fnc-tiff-to-png-converter-prd  │  fnc-invoice-classifier-prd            │   │
│  │  fnc-data-extractor-prd         │  fnc-bigquery-writer-prd               │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **secrets module** | Create Secret Manager secrets for API keys | Terraform + google_secret_manager_secret |
| **iam module** | Create service accounts with role bindings | Terraform + google_service_account |
| **gcs module** | Create buckets with lifecycle rules and notifications | Terraform + google_storage_bucket |
| **pubsub module** | Create topics, subscriptions, and DLQs | Terraform + google_pubsub_topic |
| **bigquery module** | Create dataset and tables with schemas | Terraform + google_bigquery_dataset |
| **cloud-run module** | Deploy Cloud Run v2 services | Terraform + google_cloud_run_v2_service |
| **Terragrunt root** | Backend generation, provider config, common inputs | Terragrunt HCL |
| **env.hcl** | Production-specific variable values | Terragrunt HCL |

---

## Key Decisions

### Decision 1: Production-Only Scope

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** Originally planned for both dev and prod environments. Updated scope focuses on production only.

**Choice:** Build only `environments/prod/` directory, defer dev environment.

**Rationale:**
- Reduces initial delivery scope by ~40%
- Dev environment can use `gcloud` CLI for rapid iteration (per meeting decision)
- Production is critical path for April 1 deadline
- Modules are reusable—dev can be added later

**Alternatives Rejected:**
1. Build both environments now - Rejected because timeline is tight
2. Skip IaC entirely - Rejected because production needs repeatability

**Consequences:**
- Faster time to production
- Dev team uses manual CLI for now
- Must document how to add dev environment later

---

### Decision 2: Terragrunt for Orchestration

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** Need to orchestrate 6 Terraform modules with dependencies and share common configuration.

**Choice:** Use Terragrunt with `dependency` blocks and `generate` blocks.

**Rationale:**
- DRY configuration (backend, provider defined once)
- Automatic dependency resolution with `run-all`
- Mock outputs enable parallel planning
- Industry standard for multi-environment Terraform

**Alternatives Rejected:**
1. Terraform workspaces - Rejected: Poor isolation, single state file
2. Terraform modules only - Rejected: Duplicated backend/provider config
3. Custom shell scripts - Rejected: No dependency graph, error-prone

**Consequences:**
- Team must learn Terragrunt syntax
- Additional tool dependency
- Better maintainability long-term

---

### Decision 3: GCS Backend for State

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** Terraform state must be stored remotely for team collaboration.

**Choice:** Use GCS bucket `eda-gemini-prd-tfstate` with versioning.

**Rationale:**
- Native GCP integration
- Built-in versioning for state recovery
- Locking via Cloud Storage locks
- No additional service (vs. Terraform Cloud)

**Alternatives Rejected:**
1. Local state - Rejected: Cannot share, no recovery
2. Terraform Cloud - Rejected: Additional cost, external dependency
3. S3 backend - Rejected: Cross-cloud complexity

**Consequences:**
- Must create state bucket before first `terragrunt apply`
- State bucket is a bootstrap dependency

---

### Decision 4: Module-per-Resource-Type

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** Need to decide module granularity—one big module or many small ones.

**Choice:** Six separate modules by resource type (gcs, pubsub, bigquery, cloud-run, iam, secrets).

**Rationale:**
- Single responsibility per module
- Independent testing and validation
- Parallel deployment for non-dependent modules
- Clear ownership and debugging

**Alternatives Rejected:**
1. Monolithic module - Rejected: Too complex, hard to test
2. Per-function modules - Rejected: Too granular, duplication

**Consequences:**
- More files but better organization
- Clear dependency graph
- Easier to extend for dev environment later

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `infra/terragrunt.hcl` | Create | Root Terragrunt config with backend/provider generation | @ci-cd-specialist | None |
| 2 | `infra/environments/prod/env.hcl` | Create | Production environment variables | @ci-cd-specialist | None |
| 3 | `infra/modules/secrets/main.tf` | Create | Secret Manager resources | @infra-deployer | None |
| 4 | `infra/modules/secrets/variables.tf` | Create | Secrets module variables | @infra-deployer | None |
| 5 | `infra/modules/secrets/outputs.tf` | Create | Secrets module outputs | @infra-deployer | None |
| 6 | `infra/modules/secrets/versions.tf` | Create | Secrets module version constraints | @infra-deployer | None |
| 7 | `infra/modules/iam/main.tf` | Create | Service accounts and bindings | @infra-deployer | None |
| 8 | `infra/modules/iam/variables.tf` | Create | IAM module variables | @infra-deployer | None |
| 9 | `infra/modules/iam/outputs.tf` | Create | IAM module outputs | @infra-deployer | None |
| 10 | `infra/modules/iam/versions.tf` | Create | IAM module version constraints | @infra-deployer | None |
| 11 | `infra/modules/gcs/main.tf` | Create | GCS buckets with lifecycle | @infra-deployer | None |
| 12 | `infra/modules/gcs/variables.tf` | Create | GCS module variables | @infra-deployer | None |
| 13 | `infra/modules/gcs/outputs.tf` | Create | GCS module outputs | @infra-deployer | None |
| 14 | `infra/modules/gcs/versions.tf` | Create | GCS module version constraints | @infra-deployer | None |
| 15 | `infra/modules/pubsub/main.tf` | Create | Pub/Sub topics and subscriptions | @infra-deployer | None |
| 16 | `infra/modules/pubsub/variables.tf` | Create | Pub/Sub module variables | @infra-deployer | None |
| 17 | `infra/modules/pubsub/outputs.tf` | Create | Pub/Sub module outputs | @infra-deployer | None |
| 18 | `infra/modules/pubsub/versions.tf` | Create | Pub/Sub module version constraints | @infra-deployer | None |
| 19 | `infra/modules/pubsub/dlq.tf` | Create | Dead-letter queue resources | @infra-deployer | None |
| 20 | `infra/modules/bigquery/main.tf` | Create | BigQuery dataset and tables | @infra-deployer | None |
| 21 | `infra/modules/bigquery/variables.tf` | Create | BigQuery module variables | @infra-deployer | None |
| 22 | `infra/modules/bigquery/outputs.tf` | Create | BigQuery module outputs | @infra-deployer | None |
| 23 | `infra/modules/bigquery/versions.tf` | Create | BigQuery module version constraints | @infra-deployer | None |
| 24 | `infra/modules/bigquery/schemas/` | Create | Table schema JSON files | @infra-deployer | None |
| 25 | `infra/modules/cloud-run/main.tf` | Create | Cloud Run v2 services | @infra-deployer | None |
| 26 | `infra/modules/cloud-run/variables.tf` | Create | Cloud Run module variables | @infra-deployer | None |
| 27 | `infra/modules/cloud-run/outputs.tf` | Create | Cloud Run module outputs | @infra-deployer | None |
| 28 | `infra/modules/cloud-run/versions.tf` | Create | Cloud Run module version constraints | @infra-deployer | None |
| 29 | `infra/modules/cloud-run/iam.tf` | Create | Cloud Run IAM bindings | @infra-deployer | None |
| 30 | `infra/environments/prod/secrets/terragrunt.hcl` | Create | Secrets Terragrunt wrapper | @ci-cd-specialist | 1, 2 |
| 31 | `infra/environments/prod/iam/terragrunt.hcl` | Create | IAM Terragrunt wrapper | @ci-cd-specialist | 1, 2, 30 |
| 32 | `infra/environments/prod/gcs/terragrunt.hcl` | Create | GCS Terragrunt wrapper | @ci-cd-specialist | 1, 2, 31 |
| 33 | `infra/environments/prod/pubsub/terragrunt.hcl` | Create | Pub/Sub Terragrunt wrapper | @ci-cd-specialist | 1, 2, 31 |
| 34 | `infra/environments/prod/bigquery/terragrunt.hcl` | Create | BigQuery Terragrunt wrapper | @ci-cd-specialist | 1, 2, 31 |
| 35 | `infra/environments/prod/cloud-run/terragrunt.hcl` | Create | Cloud Run Terragrunt wrapper | @ci-cd-specialist | 1, 2, 31-34 |

**Total Files:** 35

---

## Agent Assignment Rationale

| Agent | Files Assigned | Why This Agent |
|-------|----------------|----------------|
| @ci-cd-specialist | 1, 2, 30-35 | Specializes in Terragrunt config, CI/CD patterns, multi-environment setup |
| @infra-deployer | 3-29 | Specializes in Terraform modules, GCP resource provisioning, IaC patterns |

**Agent Discovery:**
- Scanned: `.claude/agents/**/*.md`
- Matched by: "Terraform", "Terragrunt", "GCP", "infrastructure", "IaC"

---

## Code Patterns

### Pattern 1: Terraform Module Structure

```hcl
# modules/{module}/versions.tf
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 5.0.0"
    }
  }
}
```

### Pattern 2: Root Terragrunt Configuration

```hcl
# infra/terragrunt.hcl
locals {
  env_config = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  project_id = local.env_config.locals.project_id
  region     = local.env_config.locals.region
  env        = local.env_config.locals.environment
}

generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  backend "gcs" {
    bucket = "${local.project_id}-tfstate"
    prefix = "${path_relative_to_include()}"
  }
}
EOF
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "google" {
  project = "${local.project_id}"
  region  = "${local.region}"
}

provider "google-beta" {
  project = "${local.project_id}"
  region  = "${local.region}"
}
EOF
}

inputs = {
  project_id = local.project_id
  region     = local.region
  env        = local.env

  labels = {
    environment = local.env
    project     = "invoice-pipeline"
    managed_by  = "terragrunt"
  }
}
```

### Pattern 3: Environment Configuration

```hcl
# infra/environments/prod/env.hcl
locals {
  environment = "prod"
  project_id  = "eda-gemini-prd"
  region      = "us-central1"

  # Production scaling
  cloud_run_settings = {
    tiff_converter = {
      memory        = "1Gi"
      cpu           = "1"
      timeout       = 300
      min_instances = 1
      max_instances = 50
      concurrency   = 1
    }
    # ... other functions
  }

  # Compliance settings
  gcs_lifecycle_days         = 90
  gcs_archive_retention_years = 7
  bigquery_partition_expiration = null  # Never expire
  enable_dead_letter_queues   = true
}
```

### Pattern 4: Terragrunt Dependency

```hcl
# infra/environments/prod/cloud-run/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

include "env" {
  path   = find_in_parent_folders("env.hcl")
  expose = true
}

dependency "iam" {
  config_path = "../iam"
  mock_outputs = {
    service_account_emails = {
      tiff_converter = "mock@project.iam.gserviceaccount.com"
    }
  }
}

dependency "pubsub" {
  config_path = "../pubsub"
  mock_outputs = {
    topic_ids = { invoice_uploaded = "mock-topic" }
  }
}

dependency "gcs" {
  config_path = "../gcs"
  mock_outputs = {
    bucket_names = { pipeline = "mock-bucket" }
  }
}

dependency "secrets" {
  config_path = "../secrets"
  mock_outputs = {
    secret_ids = { gemini_api_key = "mock-secret" }
  }
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//cloud-run"
}

inputs = {
  services         = include.env.locals.cloud_run_settings
  service_accounts = dependency.iam.outputs.service_account_emails
  pubsub_topics    = dependency.pubsub.outputs.topic_ids
  gcs_buckets      = dependency.gcs.outputs.bucket_names
  secrets          = dependency.secrets.outputs.secret_ids
}
```

### Pattern 5: Cloud Run v2 Service

```hcl
# modules/cloud-run/main.tf
resource "google_cloud_run_v2_service" "service" {
  for_each = var.services

  name     = "fnc-${each.key}-${var.env}"
  location = var.region
  project  = var.project_id

  template {
    service_account = var.service_accounts[each.key]
    timeout         = "${each.value.timeout}s"

    scaling {
      min_instance_count = each.value.min_instances
      max_instance_count = each.value.max_instances
    }

    containers {
      image = "gcr.io/${var.project_id}/${each.key}:${var.image_tag}"

      resources {
        limits = {
          memory = each.value.memory
          cpu    = each.value.cpu
        }
      }
    }

    max_instance_request_concurrency = each.value.concurrency
  }

  labels = var.labels
}
```

---

## Data Flow

```text
1. Bootstrap: Create GCS state bucket manually
   │
   ▼
2. terragrunt run-all init (in environments/prod/)
   │  - Generates backend.tf and provider.tf
   │  - Initializes all modules
   │
   ▼
3. terragrunt run-all apply
   │
   ├─ secrets module (first - no dependencies)
   │  └─ Creates 3 secrets in Secret Manager
   │
   ├─ iam module (depends on secrets)
   │  └─ Creates 5 service accounts with role bindings
   │
   ├─ gcs module (depends on iam) ──────────────┐
   │  └─ Creates 4 buckets with lifecycle       │
   │                                            │ PARALLEL
   ├─ pubsub module (depends on iam) ───────────┤
   │  └─ Creates 5 topics, subscriptions, DLQ   │
   │                                            │
   ├─ bigquery module (depends on iam) ─────────┘
   │  └─ Creates dataset and 4 tables
   │
   └─ cloud-run module (depends on all above)
      └─ Creates 4 Cloud Run services with triggers
   │
   ▼
4. Outputs available for verification
   │
   ▼
5. End-to-end testing
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|------------------|----------------|
| GCP APIs | Terraform Provider | ADC / Service Account |
| Secret Manager | Resource creation | IAM roles |
| Cloud Run | Resource creation + triggers | Service Account |
| Pub/Sub | Resource creation + subscriptions | Service Account |
| BigQuery | Resource creation + schemas | Service Account |
| GCS | Resource creation + notifications | Service Account |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|---------------|
| **Validate** | HCL syntax | All `.tf` files | `terraform validate` | 100% modules |
| **Format** | Code style | All `.tf` files | `terraform fmt -check` | 100% files |
| **Plan** | Resource creation | All modules | `terragrunt plan` | All resources |
| **Apply** | Actual deployment | All modules | `terragrunt apply` | Production |
| **Idempotency** | Re-run safety | All modules | `terragrunt plan` (post-apply) | 0 changes |
| **Destroy** | Cleanup | All modules | `terragrunt destroy` | Clean state |

### Acceptance Test Mapping

| AT-ID | Test Strategy |
|-------|--------------|
| AT-001 | `terragrunt run-all apply` succeeds |
| AT-002 | Check Cloud Run configs via `gcloud run services describe` |
| AT-003 | Run `terragrunt plan` after apply, expect "No changes" |
| AT-004 | Run cloud-run apply without iam, expect Terragrunt dependency error |
| AT-005 | Verify state in `gs://eda-gemini-prd-tfstate/` |
| AT-006 | `gcloud` list resources, check `-prd` suffix |
| AT-007 | Check Cloud Run logs for successful secret access |
| AT-008 | `gsutil lifecycle get gs://eda-gemini-prd-archive` shows 7-year |

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|-------------------|--------|
| State lock | Wait and retry, or force-unlock if stale | Yes |
| API quota | Increase quota or add delays | No |
| IAM propagation | Wait 60s for IAM changes to propagate | Yes |
| Missing dependency | Terragrunt auto-resolves order | N/A |
| Invalid config | `terraform validate` catches early | No |

---

## Configuration

| Config Key | Type | Value | Description |
|------------|------|-------|-------------|
| `project_id` | string | `eda-gemini-prd` | GCP project |
| `region` | string | `us-central1` | Primary region |
| `env` | string | `prod` | Environment suffix |
| `min_instances` | number | `1-2` | Per function |
| `max_instances` | number | `50-100` | Per function |
| `gcs_lifecycle_days` | number | `90` | Standard bucket lifecycle |
| `archive_retention_years` | number | `7` | Compliance retention |

---

## Security Considerations

- **Secrets in Secret Manager** - Never in code or environment variables
- **Least-privilege IAM** - Each function has its own service account
- **GCS bucket not public** - No `allUsers` access
- **State bucket protected** - Only deployment service account can access
- **No sensitive outputs** - Secret values not exposed in Terraform outputs

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| **State versions** | GCS versioning enabled for state recovery |
| **Resource labels** | All resources tagged with `environment`, `project`, `managed_by` |
| **Terraform logs** | `TF_LOG=INFO` for debugging |
| **Dependency graph** | `terragrunt graph-dependencies` visualizes order |

---

## Bootstrap Prerequisites

Before running `terragrunt apply`:

```bash
# 1. Create state bucket (one-time)
gsutil mb -p eda-gemini-prd -l us-central1 gs://eda-gemini-prd-tfstate
gsutil versioning set on gs://eda-gemini-prd-tfstate

# 2. Enable required APIs
gcloud services enable \
  run.googleapis.com \
  pubsub.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com \
  secretmanager.googleapis.com \
  --project=eda-gemini-prd

# 3. Authenticate
gcloud auth application-default login
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-30 | design-agent | Initial version (production-only scope) |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_TERRAFORM_TERRAGRUNT_INFRA.md`
