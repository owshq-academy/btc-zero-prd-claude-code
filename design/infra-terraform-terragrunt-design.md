# Terraform + Terragrunt Infrastructure Design

> **Version:** 1.0.0
> **Date:** January 30, 2026
> **Owner:** Pedro Lima (Platform/DevOps Lead)
> **Status:** Design Phase
> **Critical Deadline:** April 1, 2026 (Production Launch)

---

## 1. Executive Summary

### Overview

This document provides a comprehensive infrastructure design for the UberEats Invoice Processing Pipeline using Terraform modules orchestrated by Terragrunt for multi-environment deployment. The infrastructure supports a serverless, event-driven architecture on Google Cloud Platform (GCP) with complete environment isolation between dev and prod.

### Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| IaC Tool | Terraform | Industry standard, excellent GCP support |
| Multi-Environment | Terragrunt | DRY configurations, dependency management |
| State Backend | GCS | Native GCP integration, versioning support |
| Project Isolation | Separate GCP projects | Security, billing, resource isolation |
| Module Pattern | Reusable Terraform modules | Consistency, maintainability |
| Naming Convention | `{resource}-{function}-{env}` | Clear identification, environment awareness |

### Infrastructure Scope

| Category | Count | Description |
|----------|-------|-------------|
| Cloud Run Services | 4 | Pipeline processing functions |
| Pub/Sub Topics | 5 | Event-driven communication (4 pipeline + 1 debug) |
| GCS Buckets | 4 | Input, processed, archive, failed |
| BigQuery Dataset | 1 | Extracted invoice data storage |
| Service Accounts | 5 | Function-specific + shared invoker |
| Secrets | 3 | API keys and credentials |

---

## 2. Cloud Run Functions Inventory

### 2.1 Functions Overview

| Function | Purpose | Trigger | Pub/Sub Subscribe | Pub/Sub Publish |
|----------|---------|---------|-------------------|-----------------|
| `tiff-to-png-converter` | Convert TIFF invoices to PNG | `invoice-uploaded` topic | Yes | `invoice-converted` |
| `invoice-classifier` | Classify vendor type, validate quality | `invoice-converted` topic | Yes | `invoice-classified` |
| `data-extractor` | Extract data using Gemini LLM | `invoice-classified` topic | Yes | `invoice-extracted` |
| `bigquery-writer` | Write extracted data to BigQuery | `invoice-extracted` topic | Yes | None |

### 2.2 Function Runtime Specifications

| Function | Memory | Timeout | Min Instances (Dev/Prod) | Max Instances (Dev/Prod) | Concurrency |
|----------|--------|---------|--------------------------|--------------------------|-------------|
| `tiff-to-png-converter` | 1Gi | 300s | 0 / 1 | 10 / 50 | 1 |
| `invoice-classifier` | 512Mi | 120s | 0 / 1 | 10 / 50 | 10 |
| `data-extractor` | 2Gi | 300s | 0 / 2 | 10 / 100 | 1 |
| `bigquery-writer` | 512Mi | 60s | 0 / 1 | 10 / 50 | 50 |

**Notes:**
- `tiff-to-png-converter`: CPU-intensive (Pillow image processing), concurrency=1 recommended
- `data-extractor`: Memory-intensive (LLM API calls), needs 2Gi for model responses
- `bigquery-writer`: I/O-bound, high concurrency safe

### 2.3 Function Dependencies

| Function | Python Version | Key Dependencies |
|----------|---------------|------------------|
| `tiff-to-png-converter` | 3.11 | Pillow 10.x, google-cloud-storage, google-cloud-pubsub, pydantic 2.x |
| `invoice-classifier` | 3.11 | Pillow 10.x, google-cloud-storage, google-cloud-pubsub, pydantic 2.x |
| `data-extractor` | 3.11 | google-cloud-aiplatform, openai, httpx, tenacity, pydantic 2.x |
| `bigquery-writer` | 3.11 | google-cloud-bigquery, google-cloud-pubsub, pydantic 2.x |

### 2.4 Trigger Configuration

| Function | Trigger Type | Topic | Entry Point |
|----------|--------------|-------|-------------|
| `tiff-to-png-converter` | Pub/Sub CloudEvent | `invoice-uploaded` | `handle_invoice_uploaded` |
| `invoice-classifier` | Pub/Sub CloudEvent | `invoice-converted` | `handle_invoice_converted` |
| `data-extractor` | Pub/Sub CloudEvent | `invoice-classified` | `handle_invoice_classified` |
| `bigquery-writer` | Pub/Sub CloudEvent | `invoice-extracted` | `handle_invoice_extracted` |

---

## 3. GCP Resources Required

### 3.1 Cloud Run Services

#### Resource Naming Convention

| Environment | Function | Service Name |
|-------------|----------|--------------|
| Dev | tiff-to-png-converter | `fnc-tiff-to-png-converter-dev` |
| Dev | invoice-classifier | `fnc-invoice-classifier-dev` |
| Dev | data-extractor | `fnc-data-extractor-dev` |
| Dev | bigquery-writer | `fnc-bigquery-writer-dev` |
| Prod | tiff-to-png-converter | `fnc-tiff-to-png-converter-prd` |
| Prod | invoice-classifier | `fnc-invoice-classifier-prd` |
| Prod | data-extractor | `fnc-data-extractor-prd` |
| Prod | bigquery-writer | `fnc-bigquery-writer-prd` |

#### Container Images

| Function | Image Path |
|----------|------------|
| tiff-to-png-converter | `gcr.io/{project_id}/tiff-to-png-converter:{version}` |
| invoice-classifier | `gcr.io/{project_id}/invoice-classifier:{version}` |
| data-extractor | `gcr.io/{project_id}/data-extractor:{version}` |
| bigquery-writer | `gcr.io/{project_id}/bigquery-writer:{version}` |

### 3.2 Pub/Sub Topics and Subscriptions

#### Topics

| Topic Name (Dev) | Topic Name (Prod) | Purpose | Message Retention |
|------------------|-------------------|---------|-------------------|
| `eda-gemini-dev-invoice-uploaded` | `eda-gemini-prd-invoice-uploaded` | GCS upload notification | 7 days |
| `eda-gemini-dev-invoice-converted` | `eda-gemini-prd-invoice-converted` | PNG conversion complete | 7 days |
| `eda-gemini-dev-invoice-classified` | `eda-gemini-prd-invoice-classified` | Vendor classification complete | 7 days |
| `eda-gemini-dev-invoice-extracted` | `eda-gemini-prd-invoice-extracted` | LLM extraction complete | 7 days |
| `eda-gemini-dev-raw-gemini-output` | `eda-gemini-prd-raw-gemini-output` | Debug/audit raw LLM output | 7 days |

#### Subscriptions

| Subscription Name | Topic | Push Endpoint | Ack Deadline | Max Delivery Attempts |
|-------------------|-------|---------------|--------------|----------------------|
| `tiff-converter-sub` | `invoice-uploaded` | Cloud Run URL | 60s | 5 |
| `classifier-sub` | `invoice-converted` | Cloud Run URL | 60s | 5 |
| `extractor-sub` | `invoice-classified` | Cloud Run URL | 120s | 5 |
| `writer-sub` | `invoice-extracted` | Cloud Run URL | 60s | 5 |

#### Retry Policy (All Subscriptions)

| Parameter | Value |
|-----------|-------|
| Minimum Backoff | 10s |
| Maximum Backoff | 600s |

### 3.3 GCS Buckets

| Bucket Purpose | Dev Name | Prod Name | Location | Lifecycle |
|----------------|----------|-----------|----------|-----------|
| Input/Landing | `eda-gemini-dev-pipeline` | `eda-gemini-prd-pipeline` | us-central1 | 90 days |
| Processed | `eda-gemini-dev-processed` | `eda-gemini-prd-processed` | us-central1 | 90 days |
| Archive | `eda-gemini-dev-archive` | `eda-gemini-prd-archive` | us-central1 | 7 years |
| Failed | `eda-gemini-dev-failed` | `eda-gemini-prd-failed` | us-central1 | Until resolved |

#### Folder Structure (Within Pipeline Bucket)

```
{bucket}/
├── landing/              # Incoming TIFF files
├── converted/            # PNG files after conversion
├── classified/           # Files after classification
│   ├── ubereats/
│   ├── doordash/
│   ├── grubhub/
│   ├── ifood/
│   └── rappi/
├── extracted/            # JSON files after extraction
│   └── {vendor}/
├── loaded/               # Archived after BigQuery write
│   └── {year}/{month}/{vendor}/
└── failed/               # Failed processing
    ├── converter/
    ├── classifier/
    ├── extractor/
    └── writer/
```

#### GCS Notification (Eventarc)

| Bucket | Event Type | Topic |
|--------|------------|-------|
| `{pipeline-bucket}/landing/` | `OBJECT_FINALIZE` | `invoice-uploaded` |

### 3.4 BigQuery Resources

#### Dataset

| Environment | Dataset Name | Location | Partition Expiration |
|-------------|--------------|----------|---------------------|
| Dev | `ds_bq_gemini_dev` | US | 30 days |
| Prod | `ds_bq_gemini_prd` | US | Never |

#### Tables

| Table Name | Purpose | Partitioning | Clustering |
|------------|---------|--------------|------------|
| `extractions` | Primary invoice data | `processed_at` (DAY) | `vendor_type`, `invoice_id` |
| `line_items` | Invoice line items | `processed_at` (DAY) | `invoice_id` |
| `audit_log` | Processing audit trail | `timestamp` (DAY) | `status`, `function_name` |
| `metrics` | Extraction metrics | `timestamp` (DAY) | `vendor_type`, `extraction_model` |

#### Schema: extractions Table

```sql
CREATE TABLE ds_bq_gemini_{env}.extractions (
  extraction_id STRING NOT NULL,
  invoice_id STRING NOT NULL,
  vendor_type STRING NOT NULL,
  restaurant_name STRING,
  restaurant_address STRING,
  order_id STRING,
  order_date DATE,
  subtotal NUMERIC(15,2),
  delivery_fee NUMERIC(15,2),
  service_fee NUMERIC(15,2),
  tip_amount NUMERIC(15,2),
  total_amount NUMERIC(15,2),
  currency STRING,
  source_file STRING,
  extraction_model STRING,
  extraction_latency_ms INT64,
  confidence_score FLOAT64,
  processed_at TIMESTAMP,
  metadata JSON
)
PARTITION BY DATE(processed_at)
CLUSTER BY vendor_type, invoice_id;
```

#### Schema: line_items Table

```sql
CREATE TABLE ds_bq_gemini_{env}.line_items (
  line_item_id STRING NOT NULL,
  invoice_id STRING NOT NULL,
  description STRING,
  quantity INT64,
  unit_price NUMERIC(15,2),
  amount NUMERIC(15,2),
  processed_at TIMESTAMP
)
PARTITION BY DATE(processed_at)
CLUSTER BY invoice_id;
```

### 3.5 Secret Manager

| Secret Name (Dev) | Secret Name (Prod) | Purpose |
|-------------------|-------------------|---------|
| `eda-gemini-dev-gemini-api-key` | `eda-gemini-prd-gemini-api-key` | Vertex AI / Gemini API |
| `eda-gemini-dev-openrouter-api-key` | `eda-gemini-prd-openrouter-api-key` | OpenRouter fallback |
| `eda-gemini-dev-langfuse-secret` | `eda-gemini-prd-langfuse-secret` | LangFuse observability |

### 3.6 IAM Service Accounts

#### Service Accounts

| Service Account | Purpose | Environment Suffix |
|-----------------|---------|-------------------|
| `sa-tiff-converter` | TIFF to PNG function | `-dev` / `-prd` |
| `sa-classifier` | Invoice classifier function | `-dev` / `-prd` |
| `sa-extractor` | Data extractor function | `-dev` / `-prd` |
| `sa-bq-writer` | BigQuery writer function | `-dev` / `-prd` |
| `sa-pubsub-invoker` | Pub/Sub push invoker | `-dev` / `-prd` |

#### IAM Role Bindings

| Service Account | Roles |
|-----------------|-------|
| `sa-tiff-converter` | `roles/storage.objectViewer` (input bucket), `roles/storage.objectCreator` (processed bucket), `roles/pubsub.publisher` |
| `sa-classifier` | `roles/storage.objectViewer` (processed bucket), `roles/storage.objectCreator` (archive bucket), `roles/pubsub.publisher` |
| `sa-extractor` | `roles/storage.objectViewer` (classified folder), `roles/storage.objectCreator` (extracted, failed), `roles/pubsub.publisher`, `roles/aiplatform.user` |
| `sa-bq-writer` | `roles/bigquery.dataEditor`, `roles/storage.objectViewer` (extracted folder) |
| `sa-pubsub-invoker` | `roles/run.invoker` |

---

## 4. Terraform Module Structure

### 4.1 Module Hierarchy Diagram

```
infrastructure/
├── terragrunt.hcl                    # Root config (backend, provider generation)
├── modules/                          # Reusable Terraform modules
│   ├── cloud-run/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── versions.tf
│   │   └── iam.tf
│   ├── pubsub/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── versions.tf
│   │   └── dlq.tf
│   ├── gcs/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   ├── bigquery/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   ├── iam/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   └── secrets/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── versions.tf
│
└── environments/
    ├── dev/
    │   ├── env.hcl                   # Dev environment variables
    │   ├── gcs/
    │   │   └── terragrunt.hcl
    │   ├── pubsub/
    │   │   └── terragrunt.hcl
    │   ├── bigquery/
    │   │   └── terragrunt.hcl
    │   ├── iam/
    │   │   └── terragrunt.hcl
    │   ├── secrets/
    │   │   └── terragrunt.hcl
    │   └── cloud-run/
    │       └── terragrunt.hcl
    │
    └── prod/
        ├── env.hcl                   # Prod environment variables
        ├── gcs/
        │   └── terragrunt.hcl
        ├── pubsub/
        │   └── terragrunt.hcl
        ├── bigquery/
        │   └── terragrunt.hcl
        ├── iam/
        │   └── terragrunt.hcl
        ├── secrets/
        │   └── terragrunt.hcl
        └── cloud-run/
            └── terragrunt.hcl
```

### 4.2 Module Specifications

#### 4.2.1 cloud-run Module

**Purpose:** Deploy Cloud Run services with Pub/Sub triggers

**Input Variables:**

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `service_name` | string | Yes | - | Cloud Run service name |
| `project_id` | string | Yes | - | GCP project ID |
| `region` | string | Yes | - | GCP region |
| `image` | string | Yes | - | Container image URL |
| `service_account_email` | string | Yes | - | Service account for the function |
| `memory` | string | No | `"512Mi"` | Memory allocation |
| `cpu` | string | No | `"1"` | CPU allocation |
| `timeout` | number | No | `300` | Request timeout (seconds) |
| `concurrency` | number | No | `80` | Max concurrent requests per instance |
| `min_instances` | number | No | `0` | Minimum instances (cold start) |
| `max_instances` | number | No | `100` | Maximum instances |
| `env_vars` | map(string) | No | `{}` | Environment variables |
| `secrets` | list(object) | No | `[]` | Secret Manager references |

**Outputs:**

| Output | Type | Description |
|--------|------|-------------|
| `service_url` | string | Cloud Run service URL |
| `service_name` | string | Service name |
| `service_id` | string | Full resource ID |

#### 4.2.2 pubsub Module

**Purpose:** Create Pub/Sub topics with subscriptions and optional DLQ

**Input Variables:**

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `topic_name` | string | Yes | - | Pub/Sub topic name |
| `project_id` | string | Yes | - | GCP project ID |
| `message_retention_duration` | string | No | `"604800s"` | Message retention (7 days) |
| `enable_dead_letter` | bool | No | `true` | Create dead-letter topic |
| `subscriptions` | list(object) | No | `[]` | Subscription configurations |
| `labels` | map(string) | No | `{}` | Resource labels |

**Outputs:**

| Output | Type | Description |
|--------|------|-------------|
| `topic_name` | string | Topic name |
| `topic_id` | string | Full topic resource ID |
| `dlq_topic_name` | string | DLQ topic name (if enabled) |
| `subscription_names` | list(string) | List of subscription names |

#### 4.2.3 gcs Module

**Purpose:** Create GCS buckets with lifecycle rules and notifications

**Input Variables:**

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `bucket_name` | string | Yes | - | Bucket name |
| `project_id` | string | Yes | - | GCP project ID |
| `location` | string | No | `"US"` | Bucket location |
| `storage_class` | string | No | `"STANDARD"` | Storage class |
| `lifecycle_age_days` | number | No | `90` | Object lifecycle (days) |
| `versioning_enabled` | bool | No | `false` | Enable versioning |
| `notification_topic` | string | No | `null` | Pub/Sub topic for notifications |
| `notification_prefix` | string | No | `null` | Object prefix filter |
| `labels` | map(string) | No | `{}` | Resource labels |

**Outputs:**

| Output | Type | Description |
|--------|------|-------------|
| `bucket_name` | string | Bucket name |
| `bucket_url` | string | gs:// URL |
| `bucket_self_link` | string | Self link |

#### 4.2.4 bigquery Module

**Purpose:** Create BigQuery datasets and tables with schemas

**Input Variables:**

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `dataset_id` | string | Yes | - | Dataset ID |
| `project_id` | string | Yes | - | GCP project ID |
| `location` | string | No | `"US"` | Dataset location |
| `description` | string | No | `""` | Dataset description |
| `default_partition_expiration_ms` | number | No | `null` | Partition expiration |
| `tables` | list(object) | No | `[]` | Table configurations |
| `labels` | map(string) | No | `{}` | Resource labels |

**Outputs:**

| Output | Type | Description |
|--------|------|-------------|
| `dataset_id` | string | Dataset ID |
| `dataset_self_link` | string | Dataset self link |
| `table_ids` | map(string) | Map of table IDs |

#### 4.2.5 iam Module

**Purpose:** Create service accounts and IAM bindings

**Input Variables:**

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `project_id` | string | Yes | - | GCP project ID |
| `service_accounts` | list(object) | Yes | - | Service account definitions |
| `iam_bindings` | list(object) | No | `[]` | IAM role bindings |

**Outputs:**

| Output | Type | Description |
|--------|------|-------------|
| `service_account_emails` | map(string) | Map of SA emails |
| `service_account_names` | map(string) | Map of SA names |

#### 4.2.6 secrets Module

**Purpose:** Create Secret Manager secrets with versions

**Input Variables:**

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `project_id` | string | Yes | - | GCP project ID |
| `secrets` | list(object) | Yes | - | Secret definitions |
| `labels` | map(string) | No | `{}` | Resource labels |

**Outputs:**

| Output | Type | Description |
|--------|------|-------------|
| `secret_ids` | map(string) | Map of secret IDs |
| `secret_versions` | map(string) | Map of latest versions |

### 4.3 Module Dependencies

```
                    ┌─────────────┐
                    │   secrets   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │     iam     │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │     gcs     │ │   pubsub    │ │  bigquery   │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                    ┌──────▼──────┐
                    │  cloud-run  │
                    └─────────────┘
```

**Dependency Order:**
1. `secrets` - API keys must exist first
2. `iam` - Service accounts for other resources
3. `gcs`, `pubsub`, `bigquery` - Can run in parallel
4. `cloud-run` - Depends on all above

---

## 5. Terragrunt Environment Strategy

### 5.1 Directory Structure

```
infrastructure/
├── terragrunt.hcl              # Root configuration
│
├── environments/
│   ├── dev/
│   │   ├── env.hcl             # Dev-specific variables
│   │   ├── gcs/terragrunt.hcl
│   │   ├── pubsub/terragrunt.hcl
│   │   ├── bigquery/terragrunt.hcl
│   │   ├── iam/terragrunt.hcl
│   │   ├── secrets/terragrunt.hcl
│   │   └── cloud-run/terragrunt.hcl
│   │
│   └── prod/
│       ├── env.hcl             # Prod-specific variables
│       ├── gcs/terragrunt.hcl
│       ├── pubsub/terragrunt.hcl
│       ├── bigquery/terragrunt.hcl
│       ├── iam/terragrunt.hcl
│       ├── secrets/terragrunt.hcl
│       └── cloud-run/terragrunt.hcl
│
└── modules/                    # Shared Terraform modules
```

### 5.2 Root Configuration

```hcl
# infrastructure/terragrunt.hcl

locals {
  env_config = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  project_id = local.env_config.locals.project_id
  region     = local.env_config.locals.region
  env        = local.env_config.locals.environment
}

# Generate backend configuration
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

# Generate provider configuration
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

# Common inputs for all modules
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

### 5.3 Dev vs Prod Differences

#### Dev Environment (env.hcl)

```hcl
# infrastructure/environments/dev/env.hcl

locals {
  environment = "dev"
  project_id  = "eda-gemini-dev"
  region      = "us-central1"

  # Cloud Run: Minimal resources, allow cold starts
  cloud_run_settings = {
    tiff_converter = {
      memory        = "1Gi"
      cpu           = "1"
      timeout       = 300
      min_instances = 0
      max_instances = 10
      concurrency   = 1
    }
    invoice_classifier = {
      memory        = "512Mi"
      cpu           = "1"
      timeout       = 120
      min_instances = 0
      max_instances = 10
      concurrency   = 10
    }
    data_extractor = {
      memory        = "2Gi"
      cpu           = "1"
      timeout       = 300
      min_instances = 0
      max_instances = 10
      concurrency   = 1
    }
    bigquery_writer = {
      memory        = "512Mi"
      cpu           = "1"
      timeout       = 60
      min_instances = 0
      max_instances = 10
      concurrency   = 50
    }
  }

  # Storage: Shorter retention
  gcs_lifecycle_days = 30

  # Pub/Sub: Standard retention
  pubsub_message_retention = "604800s"  # 7 days

  # BigQuery: Partition expiration for cost control
  bigquery_partition_expiration_days = 30

  # DLQ: Enabled for debugging
  enable_dead_letter_queues = true
}
```

#### Prod Environment (env.hcl)

```hcl
# infrastructure/environments/prod/env.hcl

locals {
  environment = "prod"
  project_id  = "eda-gemini-prd"
  region      = "us-central1"

  # Cloud Run: Production resources, minimize cold starts
  cloud_run_settings = {
    tiff_converter = {
      memory        = "1Gi"
      cpu           = "1"
      timeout       = 300
      min_instances = 1
      max_instances = 50
      concurrency   = 1
    }
    invoice_classifier = {
      memory        = "512Mi"
      cpu           = "1"
      timeout       = 120
      min_instances = 1
      max_instances = 50
      concurrency   = 10
    }
    data_extractor = {
      memory        = "2Gi"
      cpu           = "2"
      timeout       = 300
      min_instances = 2
      max_instances = 100
      concurrency   = 1
    }
    bigquery_writer = {
      memory        = "512Mi"
      cpu           = "1"
      timeout       = 60
      min_instances = 1
      max_instances = 50
      concurrency   = 50
    }
  }

  # Storage: Extended retention for compliance
  gcs_lifecycle_days = 90
  gcs_archive_retention_years = 7

  # Pub/Sub: Standard retention
  pubsub_message_retention = "604800s"  # 7 days

  # BigQuery: No partition expiration
  bigquery_partition_expiration_days = null

  # DLQ: Enabled for production monitoring
  enable_dead_letter_queues = true
}
```

### 5.4 Variable Values Per Environment

| Variable | Dev | Prod |
|----------|-----|------|
| `project_id` | `eda-gemini-dev` | `eda-gemini-prd` |
| `region` | `us-central1` | `us-central1` |
| `state_bucket` | `eda-gemini-dev-tfstate` | `eda-gemini-prd-tfstate` |
| `extractor_min_instances` | `0` | `2` |
| `extractor_max_instances` | `10` | `100` |
| `extractor_memory` | `2Gi` | `2Gi` |
| `extractor_cpu` | `1` | `2` |
| `gcs_lifecycle_days` | `30` | `90` |
| `bq_partition_expiration` | `30 days` | `Never` |
| `archive_retention` | `1 year` | `7 years` |

### 5.5 Dependency Ordering

```hcl
# infrastructure/environments/dev/cloud-run/terragrunt.hcl

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
      tiff_converter = "mock-sa@example.iam.gserviceaccount.com"
    }
  }
}

dependency "pubsub" {
  config_path = "../pubsub"
  mock_outputs = {
    topic_ids = {
      invoice_uploaded = "mock-topic"
    }
  }
}

dependency "gcs" {
  config_path = "../gcs"
  mock_outputs = {
    bucket_names = {
      pipeline = "mock-bucket"
    }
  }
}

dependency "secrets" {
  config_path = "../secrets"
  mock_outputs = {
    secret_ids = {
      gemini_api_key = "mock-secret"
    }
  }
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//cloud-run"
}

inputs = {
  # Service configuration from env.hcl
  services = include.env.locals.cloud_run_settings

  # Dependencies
  service_accounts = dependency.iam.outputs.service_account_emails
  pubsub_topics    = dependency.pubsub.outputs.topic_ids
  gcs_buckets      = dependency.gcs.outputs.bucket_names
  secrets          = dependency.secrets.outputs.secret_ids
}
```

---

## 6. Implementation Roadmap

### 6.1 Phase Overview

| Phase | Focus | Duration | Start Date | End Date |
|-------|-------|----------|------------|----------|
| 1 | Foundation | 3 days | Feb 10, 2026 | Feb 12, 2026 |
| 2 | Storage & Messaging | 3 days | Feb 13, 2026 | Feb 15, 2026 |
| 3 | Data Warehouse | 2 days | Feb 16, 2026 | Feb 17, 2026 |
| 4 | Cloud Run Services | 4 days | Feb 18, 2026 | Feb 21, 2026 |
| 5 | Integration & Testing | 3 days | Feb 22, 2026 | Feb 24, 2026 |
| 6 | Production Deployment | 5 days | Mar 25, 2026 | Mar 31, 2026 |

### 6.2 Phase 1: Foundation (Feb 10-12)

**Deliverables:**
- [ ] Create GCP projects (dev and prod)
- [ ] Set up Terraform state buckets
- [ ] Configure root Terragrunt configuration
- [ ] Create `iam` module
- [ ] Create `secrets` module
- [ ] Deploy service accounts to dev
- [ ] Store API keys in Secret Manager

**Acceptance Criteria:**
- State bucket accessible for both environments
- Service accounts created with correct naming
- Secrets stored and accessible

### 6.3 Phase 2: Storage & Messaging (Feb 13-15)

**Deliverables:**
- [ ] Create `gcs` module
- [ ] Create `pubsub` module
- [ ] Deploy GCS buckets to dev
- [ ] Configure GCS notifications (Eventarc)
- [ ] Deploy Pub/Sub topics to dev
- [ ] Create subscriptions with retry policies

**Acceptance Criteria:**
- All 4 buckets created with correct lifecycle
- GCS notification triggers Pub/Sub
- DLQ topics created for each main topic

### 6.4 Phase 3: Data Warehouse (Feb 16-17)

**Deliverables:**
- [ ] Create `bigquery` module
- [ ] Deploy dataset to dev
- [ ] Create tables with schemas
- [ ] Configure partitioning and clustering

**Acceptance Criteria:**
- Dataset and tables created
- Schemas match extraction output
- Partitioning configured correctly

### 6.5 Phase 4: Cloud Run Services (Feb 18-21)

**Deliverables:**
- [ ] Create `cloud-run` module
- [ ] Deploy `tiff-to-png-converter` to dev
- [ ] Deploy `invoice-classifier` to dev
- [ ] Deploy `data-extractor` to dev
- [ ] Deploy `bigquery-writer` to dev
- [ ] Configure Pub/Sub push subscriptions

**Acceptance Criteria:**
- All 4 functions deployed and healthy
- Pub/Sub triggers configured
- IAM bindings correct

### 6.6 Phase 5: Integration & Testing (Feb 22-24)

**Deliverables:**
- [ ] End-to-end pipeline test in dev
- [ ] Verify GCS -> Pub/Sub -> Cloud Run flow
- [ ] Validate BigQuery data writes
- [ ] Test error handling and DLQ
- [ ] Performance testing

**Acceptance Criteria:**
- Invoice processed from upload to BigQuery
- Error handling works correctly
- Latency within targets (<30s P95)

### 6.7 Phase 6: Production Deployment (Mar 25-31)

**Deliverables:**
- [ ] Deploy all modules to prod
- [ ] Configure prod-specific scaling
- [ ] Enable monitoring and alerting
- [ ] Production validation testing
- [ ] Documentation and runbooks

**Acceptance Criteria:**
- Production environment fully operational
- Monitoring dashboards active
- Team trained on operations

### 6.8 Priority Ordering

```
HIGH PRIORITY (P0 - Critical Path)
├── GCP Project Setup
├── State Bucket Creation
├── IAM Module (service accounts)
├── GCS Module (pipeline bucket)
├── Pub/Sub Module (topics + subscriptions)
├── Cloud Run Module (all 4 functions)
└── End-to-End Testing

MEDIUM PRIORITY (P1 - Important)
├── Secrets Module
├── BigQuery Module
├── GCS Notification (Eventarc)
├── DLQ Configuration
└── Archive Bucket Setup

LOWER PRIORITY (P2 - Nice to Have for MVP)
├── Monitoring Dashboards
├── Custom Alerting
├── Cost Optimization
└── Multi-region Setup
```

---

## 7. References

### Source Documents

| Document | Path | Purpose |
|----------|------|---------|
| Cloud Run Architecture | `design/gcp-cloud-run-fncs.md` | Function specifications and data flow |
| DevOps Requirements | `notes/05-devops-infrastructure.md` | Infrastructure decisions from planning |
| Summary Requirements | `notes/summary-requirements.md` | Consolidated project requirements |
| Terraform KB | `.claude/kb/terraform/` | Terraform patterns and modules |
| Terragrunt KB | `.claude/kb/terragrunt/` | Terragrunt configuration patterns |

### External Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| Terraform GCP Provider | https://registry.terraform.io/providers/hashicorp/google/latest/docs | Provider documentation |
| Cloud Run v2 API | https://cloud.google.com/run/docs/reference/rest | Cloud Run resource specs |
| Pub/Sub API | https://cloud.google.com/pubsub/docs/reference/rest | Pub/Sub configuration |
| Terragrunt Docs | https://terragrunt.gruntwork.io/docs/ | Terragrunt best practices |

### Related Design Documents

| Document | Status | Description |
|----------|--------|-------------|
| `design/gcp-cloud-run-fncs.md` | Approved | Cloud Run functions v2 architecture |
| `CLAUDE.md` | Active | Project context and standards |
| `.claude/sdd/architecture/ARCHITECTURE.md` | Active | Overall system architecture |

---

## Appendix A: Terraform State Management

### State Bucket Configuration

| Environment | Bucket Name | Prefix Pattern |
|-------------|-------------|----------------|
| Dev | `eda-gemini-dev-tfstate` | `environments/dev/{module}` |
| Prod | `eda-gemini-prd-tfstate` | `environments/prod/{module}` |

### State Bucket Setup Script

```bash
# Create state bucket for dev
gsutil mb -p eda-gemini-dev -l us-central1 gs://eda-gemini-dev-tfstate
gsutil versioning set on gs://eda-gemini-dev-tfstate

# Create state bucket for prod
gsutil mb -p eda-gemini-prd -l us-central1 gs://eda-gemini-prd-tfstate
gsutil versioning set on gs://eda-gemini-prd-tfstate
```

---

## Appendix B: Deployment Commands

### Terragrunt Commands

```bash
# Initialize all modules in dev
cd infrastructure/environments/dev
terragrunt run-all init

# Plan all changes in dev
terragrunt run-all plan

# Apply all changes in dev (respects dependencies)
terragrunt run-all apply

# Apply specific module
cd infrastructure/environments/dev/cloud-run
terragrunt apply

# Destroy (use with caution)
terragrunt run-all destroy
```

### Module-Specific Deployment Order

```bash
# Manual deployment order if needed
cd infrastructure/environments/dev

# 1. Secrets first
cd secrets && terragrunt apply && cd ..

# 2. IAM (service accounts)
cd iam && terragrunt apply && cd ..

# 3. Storage and messaging (parallel)
cd gcs && terragrunt apply &
cd ../pubsub && terragrunt apply &
cd ../bigquery && terragrunt apply &
wait

# 4. Cloud Run (depends on above)
cd cloud-run && terragrunt apply
```

---

## Appendix C: Cost Estimates

### Monthly Cost Estimates

| Resource | Dev | Prod | Notes |
|----------|-----|------|-------|
| Cloud Run | $5-10 | $20-50 | Based on volume |
| Pub/Sub | $1 | $2-5 | Message volume |
| GCS | $2 | $10-20 | Storage + egress |
| BigQuery | $5 | $10-30 | Query costs |
| Secret Manager | <$1 | <$1 | Per-version |
| **Total** | **~$15/month** | **~$50-100/month** | |

**Assumptions:**
- Dev: 100 invoices/month for testing
- Prod: 2,000-3,500 invoices/month

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-30 | Pedro Lima | Initial design document |

---

*Generated by the-planner agent | Confidence: 0.95 (HIGH)*
