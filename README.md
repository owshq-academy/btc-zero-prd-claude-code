# Invoice Processing Pipeline

> AI-powered serverless invoice extraction for restaurant partner reconciliation

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![GCP](https://img.shields.io/badge/cloud-GCP-4285F4.svg)](https://cloud.google.com/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-623CE4.svg)](https://www.terraform.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-218%20functions-brightgreen.svg)](#testing)

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
                               │
                          ┌────┴────┐
                          │   DLQ   │ ◀── Failed messages
                          │Processor│
                          └─────────┘

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
| **Compute** | Cloud Run Functions | Serverless event-driven compute |
| **Messaging** | Pub/Sub | Event-driven communication with DLQ |
| **Storage** | GCS | File storage (input, processed, archive, failed) |
| **Data Warehouse** | BigQuery | Extracted invoice data |
| **LLM** | Gemini 2.0 Flash | Document extraction |
| **LLM Fallback** | OpenRouter (Claude 3.5/GPT-4o) | Backup provider |
| **LLMOps** | LangFuse | Distributed tracing, cost tracking, prompt management |
| **Validation** | Pydantic v2 | Structured output validation |
| **IaC** | Terraform + Terragrunt | Infrastructure provisioning |
| **CI/CD** | GitHub Actions | Automated testing and deployment |
| **Code Review** | CodeRabbit + Claude | AI-powered PR review |
| **Security** | detect-secrets, Trivy | Secret scanning, vulnerability scanning |
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

Five Cloud Run functions for scalable processing:

| Function | Trigger | Purpose |
|----------|---------|---------|
| **tiff-to-png-converter** | GCS (Eventarc) | Convert multi-page TIFF to PNG images |
| **invoice-classifier** | Pub/Sub | Detect vendor type and validate structure |
| **data-extractor** | Pub/Sub | Extract structured data using Gemini |
| **bigquery-writer** | Pub/Sub | Write validated data to BigQuery |
| **dlq-processor** | Pub/Sub (DLQ) | Handle failed messages for retry |

### Autonomous Operations (CrewAI)

Three AI agents for self-monitoring:

| Agent | Role | Output |
|-------|------|--------|
| **Triage** | Monitor logs, classify severity | Filtered events |
| **Root Cause** | Analyze patterns, find issues | Analysis report |
| **Reporter** | Format reports, notify team | Slack alerts |

---

## Observability & Metrics

### LangFuse Integration

The pipeline includes comprehensive LLM observability via LangFuse:

| Feature | Description |
|---------|-------------|
| **Distributed Tracing** | W3C trace context propagation across all 5 functions |
| **Session Grouping** | Related invoices grouped by session ID |
| **Cost Tracking** | Token usage and cost per extraction via `usage_details` |
| **Prompt Management** | Versioned prompts with production/staging labels |
| **Confidence Scoring** | Per-extraction confidence scores (0.0-1.0) |
| **Silent Fallback** | Observability errors never block invoice processing |

### Pipeline Metrics

Each function emits structured logs with key metrics:

```json
{
  "source_file": "gs://invoices-input/invoice.tiff",
  "latency_ms": 2345,
  "llm_latency_ms": 1890,
  "total_input_bytes": 524288,
  "confidence": 0.95,
  "provider": "gemini",
  "trace_id": "abc123..."
}
```

| Metric | Description |
|--------|-------------|
| `latency_ms` | Total function execution time |
| `llm_latency_ms` | LLM API call time only |
| `total_input_bytes` | Total size of input images |
| `confidence` | Extraction confidence score |
| `trace_id` | Distributed trace identifier |

### Extraction Scores

The pipeline tracks multiple quality scores per extraction:

| Score | Description |
|-------|-------------|
| `extraction_confidence` | Overall extraction confidence (0.0-1.0) |
| `field_completeness` | Percentage of optional fields populated |
| `validation_success` | Boolean: passed Pydantic validation |

---

## CLI Reference

### `invoice-extract extract`

Extract data from a single invoice file.

```bash
invoice-extract extract <INPUT_FILE> [OPTIONS]

# Options:
  --output-dir PATH       Output directory for JSON [default: data/output]
  --processed-dir PATH    Directory for processed images [default: data/processed]
  --errors-dir PATH       Directory for error logs [default: data/errors]
  --vendor TEXT           Vendor type: ubereats/doordash/grubhub/ifood/rappi/auto
  --gemini-project TEXT   GCP project ID (or GOOGLE_CLOUD_PROJECT env var)
  --openrouter-key TEXT   OpenRouter API key (required, or OPENROUTER_API_KEY env var)

# Examples:
invoice-extract extract invoice.tiff
invoice-extract extract invoice.tiff --vendor ubereats --output-dir results/
invoice-extract extract invoice.tiff --gemini-project my-project
```

### `invoice-extract batch`

Process all invoices in a directory.

```bash
invoice-extract batch <INPUT_DIR> [OPTIONS]

# Examples:
invoice-extract batch data/input/
invoice-extract batch invoices/ --vendor doordash --output-dir results/
```

### `invoice-extract validate`

Validate a JSON extraction result against schema and business rules.

```bash
invoice-extract validate <JSON_FILE>

# Examples:
invoice-extract validate data/output/UE-2026-001234.json
```

---

## Project Structure

```text
btc-zero-prd-claude-code/
├── src/                           # Main source code
│   └── invoice_extractor/         # CLI extraction tool
│       ├── cli.py                 # Command-line interface
│       ├── extractor.py           # Extraction logic
│       ├── image_processor.py     # Image processing
│       ├── llm_gateway.py         # LLM abstraction
│       ├── models.py              # Pydantic models
│       └── validator.py           # Validation logic
│
├── functions/                     # Cloud Run Functions
│   └── gcp/v1/
│       ├── src/functions/         # 5 Cloud Run functions
│       │   ├── tiff_to_png/       # Image conversion
│       │   ├── invoice_classifier/ # Vendor detection
│       │   ├── data_extractor/    # LLM extraction
│       │   ├── bigquery_writer/   # Data warehouse writer
│       │   └── dlq_processor/     # Dead Letter Queue handler
│       └── src/shared/            # Shared utilities
│           ├── adapters/          # GCS, Pub/Sub, BigQuery, LLM, Observability
│           ├── schemas/           # Pydantic models (invoice, messages)
│           └── utils/             # Logging, config, GCS utilities
│
├── gen/                           # Code generation tools
│   └── synthetic_invoice_gen/     # Generate synthetic test invoices
│       └── src/invoice_gen/       # Invoice generation library
│
├── tests/                         # Test suites
│   └── smoke/                     # End-to-end smoke tests
│       ├── cli.py                 # Smoke test CLI
│       ├── runner.py              # Test orchestrator
│       ├── stages/                # Pipeline test stages
│       │   ├── generate.py        # Generate test invoices
│       │   ├── upload.py          # Upload to GCS
│       │   ├── process.py         # Trigger processing
│       │   ├── validate.py        # Validate results
│       │   ├── bigquery.py        # Check BigQuery
│       │   └── logging.py         # Check logs
│       └── validators/            # Field validation
│
├── infra/                         # Infrastructure as Code
│   ├── modules/                   # Terraform modules
│   │   ├── bigquery/              # BigQuery dataset/tables
│   │   ├── cloud-run/             # Cloud Run functions
│   │   ├── gcs/                   # GCS buckets
│   │   ├── iam/                   # Service accounts & roles
│   │   ├── pubsub/                # Topics, subs, DLQ
│   │   └── secrets/               # Secret Manager
│   └── environments/              # Terragrunt environments
│       └── prod/                  # Production config
│
├── design/                        # Architecture documents
│   ├── gcp-cloud-run-fncs.md      # Cloud Run functions design
│   ├── invoice-extractor-design.md
│   ├── gcp-deployment-requirements.md
│   └── infra-terraform-terragrunt-design.md
│
├── notes/                         # Project meeting notes
│   ├── 01-business-kickoff.md     # Business requirements
│   ├── 02-technical-architecture.md
│   ├── 03-data-pipeline-process.md
│   ├── 04-data-ml-strategy.md
│   ├── 05-devops-infrastructure.md
│   ├── 06-autonomous-dataops.md
│   └── summary-requirements.md    # Consolidated requirements
│
├── examples/                      # Sample invoice files
│   ├── ubereats_*.tiff            # 2 UberEats invoices
│   ├── doordash_*.tiff            # 2 DoorDash invoices
│   ├── grubhub_*.tiff             # 2 Grubhub invoices
│   ├── ifood_*.tiff               # 2 iFood invoices
│   └── rappi_*.tiff               # 2 Rappi invoices
│
├── .github/                       # GitHub configuration
│   ├── workflows/                 # CI/CD workflows
│   │   ├── ci.yaml                # Lint, test, build, security
│   │   ├── cd-dev.yaml            # Deploy to dev
│   │   ├── cd-prod.yaml           # Deploy to production
│   │   ├── terraform.yaml         # Infrastructure changes
│   │   ├── claude-review.yaml     # AI code review
│   │   └── smoke-tests.yaml       # E2E smoke tests
│   ├── CODEOWNERS                 # Code ownership
│   └── dependabot.yml             # Dependency updates
│
├── .claude/                       # Claude Code ecosystem
│   ├── agents/                    # 40 specialized AI agents
│   ├── commands/                  # 13 slash commands
│   ├── kb/                        # 8 knowledge base domains
│   └── sdd/                       # Spec-Driven Development
│
├── pyproject.toml                 # Project configuration
├── .pre-commit-config.yaml        # Pre-commit hooks
├── .coderabbit.yaml               # CodeRabbit configuration
└── .secrets.baseline              # detect-secrets baseline
```

---

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install

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

### Testing

The project includes **218 test functions** across multiple test suites:

| Suite | Location | Purpose |
|-------|----------|---------|
| Unit Tests | `src/invoice_extractor/tests/` | Invoice extractor logic |
| Function Tests | `functions/gcp/v1/tests/unit/` | Cloud Run function logic |
| Integration Tests | `functions/gcp/v1/tests/integration/` | Cross-function workflows |
| Generator Tests | `gen/synthetic_invoice_gen/tests/` | Invoice generator |
| Smoke Tests | `tests/smoke/` | End-to-end pipeline |

```bash
# Run all tests
pytest -v

# Run specific test suite
pytest functions/gcp/v1/tests/unit/ -v

# Run with coverage report
pytest --cov=src --cov=functions/gcp/v1/src --cov-report=html
```

### Pre-commit Hooks

The project uses pre-commit hooks for quality enforcement:

```yaml
# Installed hooks:
- ruff (linting + formatting)
- detect-secrets (prevent secret commits)
- trailing-whitespace
- end-of-file-fixer
- check-yaml
- check-added-large-files
```

### Code Quality

The project uses:

- **Ruff** for linting (E, F, I, UP, B, SIM rules)
- **mypy** for type checking
- **pytest** for testing
- **Pydantic v2** for data validation
- **Type hints** on all function signatures
- **detect-secrets** for secret scanning

---

## CI/CD Pipeline

### GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **CI Pipeline** | PR to main | Lint, type check, unit tests, Docker build, security scan |
| **CD Dev** | Push to main | Deploy to dev environment |
| **CD Prod** | Manual/tag | Deploy to production |
| **Terraform** | infra/** changes | Plan and apply infrastructure |
| **Claude Review** | PR | AI-powered code review |
| **Smoke Tests** | Workflow dispatch | End-to-end pipeline validation |

### CI Pipeline Stages

```text
┌─────────┐   ┌────────────┐   ┌────────────┐   ┌──────────────┐   ┌───────────────┐
│  Lint   │──▶│ Type Check │──▶│ Unit Tests │──▶│ Docker Build │──▶│ Security Scan │
│ (Ruff)  │   │   (mypy)   │   │  (pytest)  │   │ (5 images)   │   │   (Trivy)     │
└─────────┘   └────────────┘   └────────────┘   └──────────────┘   └───────────────┘
```

### Code Review

All PRs are reviewed by:
- **CodeRabbit** - AI-powered static analysis
- **Claude Code** - Architectural review via GitHub Actions

---

## Infrastructure

### Terraform Modules

| Module | Purpose |
|--------|---------|
| `bigquery` | BigQuery dataset and tables |
| `cloud-run` | Cloud Run function definitions |
| `gcs` | GCS bucket configurations |
| `iam` | Service accounts and permissions |
| `pubsub` | Pub/Sub topics, subscriptions, DLQ |
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

## Troubleshooting

### Common Issues

#### LLM Extraction Fails

```bash
# Check OpenRouter API key is set
echo $OPENROUTER_API_KEY

# Test with verbose logging
invoice-extract extract invoice.tiff 2>&1 | grep -i error
```

#### Cloud Run Function Timeout

```bash
# Check function logs
gcloud functions logs read data-extractor --limit 50

# Increase timeout (max 540s for 2nd gen)
gcloud functions deploy data-extractor --timeout=540s
```

#### LangFuse Not Recording Traces

```bash
# Verify credentials
echo $LANGFUSE_PUBLIC_KEY
echo $LANGFUSE_SECRET_KEY

# Check auth
python -c "from langfuse import Langfuse; print(Langfuse().auth_check())"
```

#### Pydantic Validation Errors

```bash
# Validate extracted JSON
invoice-extract validate data/output/invoice.json

# Check schema compatibility
python -c "from shared.schemas.invoice import ExtractedInvoice; print(ExtractedInvoice.model_json_schema())"
```

### Debug Mode

Enable verbose logging:

```bash
export LOG_LEVEL=DEBUG
invoice-extract extract invoice.tiff
```

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
| Jan 31, 2026 | All 5 functions implemented |
| Feb 28, 2026 | MVP demo to stakeholders |
| Mar 15, 2026 | Accuracy validation complete |
| **Apr 1, 2026** | **Production launch** |
| Apr 30, 2026 | CrewAI pilot complete |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Install pre-commit hooks (`pre-commit install`)
4. Run linting and tests (`ruff check . && pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

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
