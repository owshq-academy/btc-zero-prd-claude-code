# Invoice Processing Pipeline

> AI-powered serverless invoice extraction for restaurant partner reconciliation

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![GCP](https://img.shields.io/badge/cloud-GCP-4285F4.svg)](https://cloud.google.com/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-623CE4.svg)](https://www.terraform.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

The Invoice Processing Pipeline automates data extraction from delivery platform invoices (UberEats, DoorDash, Grubhub, iFood, Rappi) using **Gemini 2.0 Flash** vision AI with **Pydantic validation**.

### Business Problem

- **3 FTEs** spend 80% of time on manual data entry from delivery platform invoices
- **R$45,000+** in reconciliation errors quarterly
- **2,000+ invoices/month** (growing to 3,500 by end of year)

### Solution

Cloud-native serverless pipeline achieving:

| Metric | Target |
|--------|--------|
| Extraction accuracy | ≥ 90% |
| Processing latency P95 | < 30 seconds |
| Cost per invoice | < $0.01 |
| Manual processing reduction | > 80% |

---

## Architecture

```text
INGESTION          PROCESSING                              STORAGE
─────────          ──────────                              ───────

┌───────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ TIFF  │──▶│ TIFF→PNG │──▶│ CLASSIFY │──▶│ EXTRACT  │──▶│  WRITE   │──▶ BigQuery
│ (GCS) │   │          │   │          │   │ (Gemini) │   │          │
└───────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
    │           │              │              │              │
    └───────────┴──────────────┴──────────────┴──────────────┘
                          Pub/Sub (events)

OBSERVABILITY                              AUTONOMOUS OPS
─────────────                              ──────────────

┌───────────┐  ┌───────────┐  ┌───────────┐    ┌─────────┐  ┌───────────┐  ┌──────────┐
│ LangFuse  │  │Cloud Logs │  │ Metrics   │    │ TRIAGE  │─▶│ROOT CAUSE │─▶│ REPORTER │─▶ Slack
└───────────┘  └───────────┘  └───────────┘    └─────────┘  └───────────┘  └──────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Cloud** | Google Cloud Platform | Primary infrastructure |
| **Compute** | Cloud Run | Serverless functions |
| **Messaging** | Pub/Sub | Event-driven communication |
| **Storage** | GCS | File storage (input, processed, archive) |
| **Data Warehouse** | BigQuery | Extracted invoice data |
| **LLM** | Gemini 2.0 Flash | Document extraction |
| **LLM Fallback** | OpenRouter (Claude 3.5/GPT-4o) | Backup provider |
| **LLMOps** | LangFuse | LLM observability |
| **Validation** | Pydantic v2 | Structured output validation |
| **IaC** | Terraform + Terragrunt | Infrastructure provisioning |
| **CI/CD** | GitHub Actions | Automated testing and deployment |
| **Code Review** | CodeRabbit | AI-powered PR review |
| **Autonomous Ops** | CrewAI | AI agents for monitoring |

---

## Quick Start

### Prerequisites

- Python 3.11+
- OpenRouter API key (required)
- GCP project with Vertex AI enabled (optional, for Gemini)

### Installation

```bash
# Clone the repository
git clone https://github.com/owshq-academy/btc-zero-prd-claude-code.git
cd btc-zero-prd-claude-code

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .

# Install dev dependencies (optional)
pip install -e ".[dev]"
```

### Environment Setup

Create a `.env` file:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Optional (for Gemini)
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GCP_REGION=us-central1

# Optional (for LangFuse observability)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

### Basic Usage

```bash
# Extract a single invoice
invoice-extract extract examples/ubereats_INV-UE-2EE7F3_20260121.tiff

# Batch process all invoices in a directory
invoice-extract batch examples/ --vendor ubereats

# Validate an extracted JSON file
invoice-extract validate data/output/UE-2026-001234.json
```

---

## Features

### AI-Powered Extraction

- **Multi-modal vision AI** using Gemini 2.0 Flash for document understanding
- **Vendor-specific prompts** optimized for UberEats, DoorDash, Grubhub, iFood, and Rappi
- **Automatic fallback** to OpenRouter when primary provider fails

### Schema Validation

- **Pydantic v2 models** with strict type validation
- **Business rule validation** (date logic, commission calculations, totals)
- **Confidence scoring** per field for quality assurance

### Extraction Schema

| Field | Type | Description |
|-------|------|-------------|
| `invoice_id` | String | Unique identifier (e.g., "UE-2026-001234") |
| `vendor_name` | String | Restaurant or vendor name |
| `vendor_type` | Enum | ubereats/doordash/grubhub/ifood/rappi/other |
| `invoice_date` | Date | Invoice issue date |
| `due_date` | Date | Payment due date |
| `subtotal` | Decimal | Sum before tax/commission |
| `tax_amount` | Decimal | Tax amount |
| `commission_rate` | Decimal | Platform commission (0.0-1.0) |
| `commission_amount` | Decimal | Calculated commission |
| `total_amount` | Decimal | Final invoice total |
| `currency` | String | BRL, USD, EUR, etc. |
| `line_items` | Array | Individual line items |

### Serverless Pipeline

Four Cloud Run functions for scalable processing:

1. **tiff-to-png-converter** - Convert multi-page TIFF to PNG images
2. **invoice-classifier** - Detect vendor type and validate structure
3. **data-extractor** - Extract structured data using Gemini
4. **bigquery-writer** - Write validated data to BigQuery

### Autonomous Operations (CrewAI)

Three AI agents for self-monitoring:

| Agent | Role | Output |
|-------|------|--------|
| **Triage** | Monitor logs, classify severity | Filtered events |
| **Root Cause** | Analyze patterns, find issues | Analysis report |
| **Reporter** | Format reports, notify team | Slack alerts |

---

## Project Structure

```text
btc-zero-prd-claude-code/
├── src/                           # Main source code
│   └── invoice_extractor/         # CLI extraction tool
│
├── functions/                     # Cloud Run functions
│   └── gcp/v1/
│       ├── src/functions/         # Function implementations
│       │   ├── tiff_to_png/       # Image conversion
│       │   ├── invoice_classifier/ # Vendor detection
│       │   ├── data_extractor/    # LLM extraction
│       │   └── bigquery_writer/   # Data warehouse writer
│       └── src/shared/            # Shared utilities
│
├── gen/                           # Code generation tools
│   └── synthetic_invoice_gen/     # Generate test invoices
│
├── infra/                         # Infrastructure as Code
│   ├── modules/                   # Terraform modules
│   │   ├── cloud-run/             # Cloud Run definitions
│   │   ├── pubsub/                # Pub/Sub topics
│   │   ├── gcs/                   # GCS buckets
│   │   ├── bigquery/              # BigQuery dataset
│   │   ├── iam/                   # Service accounts
│   │   └── secrets/               # Secret Manager
│   └── environments/              # Terragrunt environments
│       ├── dev/
│       └── prod/
│
├── tests/                         # Test suites
│   └── smoke/                     # End-to-end smoke tests
│
├── design/                        # Architecture documents
├── notes/                         # Meeting notes & requirements
├── examples/                      # Sample invoice files (10 TIFFs)
├── data/                          # Local data directories
│
└── .claude/                       # Claude Code ecosystem
    ├── agents/                    # 40 specialized AI agents
    ├── commands/                  # 12 slash commands
    ├── kb/                        # 8 knowledge base domains
    └── sdd/                       # Spec-Driven Development
```

---

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run linter
ruff check .

# Run formatter check
ruff format --check .

# Run tests
pytest -v --tb=short

# Run tests with coverage
pytest --cov=src --cov-report=term-missing
```

### Generate Synthetic Test Data

```bash
cd gen/synthetic_invoice_gen
pip install -e .

# Generate 10 test invoices
invoice-gen generate --count 10 --output ../../examples/

# Generate specific vendor
invoice-gen generate --vendor ubereats --count 5
```

### Smoke Tests

End-to-end smoke tests validate the complete pipeline:

```bash
# Run smoke tests against dev environment
pytest tests/smoke/ -v

# Run with specific vendor
pytest tests/smoke/ -v --vendor ubereats

# Skip Cloud Logging checks
pytest tests/smoke/ -v --skip-logging
```

**Smoke Test Stages:**

1. **Generate** - Create synthetic invoice
2. **Upload** - Upload TIFF to GCS
3. **Process** - Poll for extraction completion
4. **Validate** - Compare extraction vs ground truth
5. **BigQuery** - Verify row in BigQuery
6. **Logging** - Check for pipeline errors

### Code Quality

The project uses:

- **Ruff** for linting (E, F, I, UP, B, SIM rules)
- **mypy** for type checking
- **pytest** for testing
- **Pydantic v2** for data validation
- **Type hints** on all function signatures

---

## CI/CD Pipeline

### GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **CI Pipeline** | PR to main | Lint, type check, unit tests, Docker build, security scan |
| **CD Dev** | Push to main | Deploy to dev environment |
| **CD Prod** | Manual/tag | Deploy to production |
| **Terraform** | infra/** changes | Plan and apply infrastructure |
| **Claude Review** | PR | AI code review |

### CI Pipeline Stages

```text
┌─────────┐   ┌────────────┐   ┌────────────┐   ┌──────────────┐   ┌───────────────┐
│  Lint   │──▶│ Type Check │──▶│ Unit Tests │──▶│ Docker Build │──▶│ Security Scan │
│ (Ruff)  │   │   (mypy)   │   │  (pytest)  │   │  (4 images)  │   │   (Trivy)     │
└─────────┘   └────────────┘   └────────────┘   └──────────────┘   └───────────────┘
```

---

## Infrastructure

### Terraform Modules

| Module | Purpose |
|--------|---------|
| `cloud-run` | Cloud Run function definitions |
| `pubsub` | Pub/Sub topics and subscriptions |
| `gcs` | GCS bucket configurations |
| `bigquery` | BigQuery dataset and tables |
| `iam` | Service accounts and permissions |
| `secrets` | Secret Manager secrets |

### GCS Buckets

| Bucket | Purpose | Retention |
|--------|---------|-----------|
| `gs://invoices-input` | Raw TIFF landing zone | 30 days |
| `gs://invoices-processed` | Converted PNG files | 90 days |
| `gs://invoices-archive` | Compliance archive | 7 years |
| `gs://invoices-failed` | Failed processing | Until resolved |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key for LLM access |
| `GOOGLE_CLOUD_PROJECT` | No | GCP project ID for Gemini |
| `GCP_REGION` | No | GCP region (default: us-central1) |
| `LANGFUSE_PUBLIC_KEY` | No | LangFuse observability key |
| `LANGFUSE_SECRET_KEY` | No | LangFuse secret key |

---

## Documentation

| Document | Description |
|----------|-------------|
| [Summary Requirements](notes/summary-requirements.md) | Consolidated requirements from 6 planning meetings |
| [Cloud Run Architecture](design/gcp-cloud-run-fncs.md) | Detailed Cloud Run function design |
| [Invoice Extractor Design](design/invoice-extractor-design.md) | Extraction pipeline architecture |
| [Deployment Requirements](design/gcp-deployment-requirements.md) | GCP deployment specifications |
| [Terraform Design](design/infra-terraform-terragrunt-design.md) | Infrastructure as Code design |

---

## Timeline

| Date | Milestone |
|------|-----------|
| Jan 15, 2026 | Project kickoff |
| Feb 7, 2026 | All 4 functions implemented |
| Feb 28, 2026 | MVP demo to stakeholders |
| Mar 15, 2026 | Accuracy validation complete |
| **Apr 1, 2026** | **Production launch** |
| Apr 30, 2026 | CrewAI pilot complete |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run linting and tests (`ruff check . && pytest`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Code Review

All PRs are reviewed by:
- **CodeRabbit** - AI-powered static analysis
- **Claude Code** - Architectural review

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Team

| Name | Role |
|------|------|
| Marina Santos | Product Manager |
| João Silva | Senior Data Engineer |
| Ana Costa | ML Engineer |
| Pedro Lima | Platform/DevOps Lead |
| Carlos Ferreira | Business Stakeholder |

---

> **Built with AI assistance using [Claude Code](https://claude.ai/code)**
