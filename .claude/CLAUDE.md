# UberEats Invoice Processing Pipeline

> AI-powered serverless invoice extraction for restaurant partner reconciliation

---

## Project Context

**Business Problem:** 3 FTEs spend 80% of time on manual data entry from delivery platform invoices, causing R$45,000+ in reconciliation errors quarterly.

**Solution:** Cloud-native serverless pipeline using Gemini 2.0 Flash for document extraction with autonomous monitoring via CrewAI.

**Critical Deadline:** April 1, 2026 (Q2 financial close)

**Requirements:** See [notes/summary-requirements.md](notes/summary-requirements.md) for consolidated requirements from 6 planning meetings.

---

## Architecture Overview

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

| Stage | Technology | Purpose |
| ----- | ---------- | ------- |
| Cloud | GCP | Primary infrastructure |
| Compute | Cloud Run Functions | Serverless event-driven functions |
| Messaging | Pub/Sub | Event-driven pipeline with DLQ |
| Storage | GCS | File storage (input, processed, archive) |
| Data Warehouse | BigQuery | Extracted invoice data |
| LLM | Gemini 2.0 Flash | Document extraction |
| LLM Fallback | OpenRouter | Backup provider |
| LLMOps | LangFuse | LLM observability |
| Validation | Pydantic v2 | Structured output validation |
| IaC | Terraform + Terragrunt | Infrastructure provisioning |
| Autonomous Ops | CrewAI | AI agents for monitoring |

---

## Project Structure

```text
btc-zero-prd-claude-code/
├── src/                           # Main source code
│   ├── __init__.py
│   └── invoice_extractor/         # Core extraction library
│       ├── cli.py                 # CLI interface
│       ├── extractor.py           # Extraction logic
│       ├── image_processor.py     # Image processing
│       ├── llm_gateway.py         # LLM abstraction
│       ├── models.py              # Pydantic models
│       ├── validator.py           # Validation logic
│       └── tests/                 # Unit & integration tests
│
├── functions/                     # Cloud Run Functions
│   └── gcp/v1/                    # GCP functions v1
│       ├── src/
│       │   ├── functions/         # 5 Cloud Run functions
│       │   │   ├── tiff_to_png/   # TIFF→PNG converter
│       │   │   ├── invoice_classifier/  # Document classification
│       │   │   ├── data_extractor/      # Gemini extraction
│       │   │   ├── bigquery_writer/     # BigQuery loader
│       │   │   └── dlq_processor/       # Dead Letter Queue handler
│       │   └── shared/            # Shared utilities
│       │       ├── adapters/      # GCS, Pub/Sub, BigQuery, LLM
│       │       ├── schemas/       # Pydantic models
│       │       └── utils/         # Logging, GCS utils
│       └── tests/                 # Function tests
│
├── gen/                           # Code generation tools
│   └── synthetic_invoice_gen/     # Synthetic test data generator
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
├── design/                        # Architecture design documents
│   ├── gcp-cloud-run-fncs.md      # Cloud Run functions design
│   ├── invoice-extractor-design.md
│   ├── invoice-extractor-requirements.md
│   ├── gcp-deployment-requirements.md
│   ├── infra-terraform-terragrunt-design.md
│   └── data-ops-crew-ai-requirements.md
│
├── notes/                         # Project meeting notes
│   ├── 01-business-kickoff.md
│   ├── 02-technical-architecture.md
│   ├── 03-data-pipeline-process.md
│   ├── 04-data-ml-strategy.md
│   ├── 05-devops-infrastructure.md
│   ├── 06-autonomous-dataops.md
│   └── summary-requirements.md    # Consolidated requirements
│
├── archive/                       # Historical versions
│   ├── sdd-agent-spec-v4.2.zip
│   └── dev-loop-v1.1.zip
│
├── .claude/                       # Claude Code ecosystem
│   ├── agents/                    # 40 specialized agents
│   │   ├── ai-ml/                 # AI/ML specialists (4)
│   │   ├── aws/                   # AWS/cloud specialists (4)
│   │   ├── code-quality/          # Code review, testing (6)
│   │   ├── communication/         # Documentation, planning (3)
│   │   ├── data-engineering/      # Spark, Lakeflow, Medallion (8)
│   │   ├── dev/                   # Dev Loop agents (2)
│   │   ├── domain/                # Project-specific agents (5)
│   │   ├── exploration/           # Codebase exploration (2)
│   │   └── workflow/              # SDD pipeline agents (6)
│   │
│   ├── commands/                  # 13 slash commands
│   │   ├── core/                  # /memory, /sync-context, /readme-maker
│   │   ├── dev/                   # /dev (Dev Loop)
│   │   ├── knowledge/             # /create-kb
│   │   ├── review/                # /review
│   │   └── workflow/              # SDD commands
│   │
│   ├── kb/                        # Knowledge Base (8 domains)
│   │   ├── _templates/
│   │   ├── pydantic/
│   │   ├── gcp/
│   │   ├── gemini/
│   │   ├── langfuse/
│   │   ├── terraform/
│   │   ├── terragrunt/
│   │   ├── crewai/
│   │   └── openrouter/
│   │
│   ├── sdd/                       # Spec-Driven Development
│   │   ├── architecture/
│   │   ├── features/              # Active DEFINE/DESIGN docs
│   │   ├── reports/               # BUILD reports
│   │   ├── archive/               # 5 shipped features
│   │   ├── examples/
│   │   └── templates/
│   │
│   └── dev/                       # Dev Loop (Level 2)
│       ├── tasks/
│       ├── progress/
│       ├── logs/
│       ├── examples/
│       └── templates/
│
└── pyproject.toml                 # Project configuration
```

---

## Cloud Run Functions (GCP v1)

| Function | Trigger | Purpose |
| -------- | ------- | ------- |
| `tiff_to_png` | GCS (eventarc) | Convert TIFF to PNG for LLM processing |
| `invoice_classifier` | Pub/Sub | Classify document type (invoice vs other) |
| `data_extractor` | Pub/Sub | Extract data using Gemini 2.0 Flash |
| `bigquery_writer` | Pub/Sub | Write extracted data to BigQuery |
| `dlq_processor` | Pub/Sub (DLQ) | Handle failed messages for retry |

### Shared Components

| Component | Path | Purpose |
| --------- | ---- | ------- |
| Storage Adapter | `shared/adapters/storage.py` | GCS operations |
| Messaging Adapter | `shared/adapters/messaging.py` | Pub/Sub operations |
| BigQuery Adapter | `shared/adapters/bigquery.py` | BigQuery operations |
| LLM Adapter | `shared/adapters/llm.py` | Gemini/OpenRouter abstraction |
| Observability | `shared/adapters/observability.py` | LangFuse integration |
| Invoice Schema | `shared/schemas/invoice.py` | Pydantic extraction models |
| Message Schema | `shared/schemas/messages.py` | Pub/Sub message models |
| Timing Utilities | `shared/utils/timing.py` | Latency and file size tracking |

---

## Active Features (In Progress)

| Feature | Status | Description |
| ------- | ------ | ----------- |
| PIPELINE_OBSERVABILITY_METRICS | Ready for Design | Latency timing (ms) and file size metrics for all pipeline functions |

---

## Shipped Features (SDD Archive)

| Feature | Shipped | Description |
| ------- | ------- | ----------- |
| INVOICE_PIPELINE | 2026-01-30 | Core 4-function pipeline |
| GCS_UPLOAD | 2026-01-31 | GCS upload for invoice generator |
| LANGFUSE_OBSERVABILITY | 2026-01-31 | LLM observability integration |
| SMOKE_TEST | 2026-01-31 | End-to-end smoke test framework |
| TERRAFORM_TERRAGRUNT_INFRA | 2026-01-31 | Infrastructure as Code |

---

## Development Workflows

### AgentSpec 4.1 (Spec-Driven Development)

5-phase structured workflow for features requiring traceability:

```text
/brainstorm → /define → /design → /build → /ship
  (Opus)      (Opus)    (Opus)   (Sonnet)  (Haiku)
```

| Command | Phase | Purpose |
|---------|-------|---------|
| `/brainstorm` | 0 | Explore ideas through dialogue (optional) |
| `/define` | 1 | Capture and validate requirements |
| `/design` | 2 | Create architecture and specification |
| `/build` | 3 | Execute implementation with verification |
| `/ship` | 4 | Archive with lessons learned |
| `/iterate` | Any | Update documents when changes needed |

**Artifacts:** `.claude/sdd/features/` and `.claude/sdd/archive/`

### Dev Loop (Level 2 Agentic Development)

Structured iteration with PROMPT.md files and session recovery:

```bash
# Let the crafter guide you
/dev "I want to build a date parser utility"

# Execute existing PROMPT
/dev tasks/PROMPT_DATE_PARSER.md

# Resume interrupted session
/dev tasks/PROMPT_DATE_PARSER.md --resume
```

**When to use:**
- KB building
- Prototypes
- Single features
- Utilities and parsers

---

## Agent Usage Guidelines

### Available Agents by Category

| Category | Agents | Use When |
| -------- | ------ | -------- |
| **Workflow** | brainstorm-agent, define-agent, design-agent, build-agent, ship-agent, iterate-agent | Building features with SDD |
| **Code Quality** | code-reviewer, code-cleaner, code-documenter, dual-reviewer, python-developer, test-generator | Improving code quality |
| **Data Engineering** | spark-specialist, spark-troubleshooter, spark-performance-analyzer, spark-streaming-architect, lakeflow-architect, lakeflow-expert, lakeflow-pipeline-builder, medallion-architect | Spark/Lakeflow work |
| **AI/ML** | llm-specialist, genai-architect, ai-prompt-specialist, ai-data-engineer | LLM prompts, AI systems |
| **AWS** | aws-deployer, aws-lambda-architect, lambda-builder, ci-cd-specialist | AWS deployments |
| **Communication** | adaptive-explainer, meeting-analyst, the-planner | Explanations, planning |
| **Domain** | pipeline-architect, function-developer, extraction-specialist, infra-deployer, dataops-builder | Project-specific tasks |
| **Exploration** | codebase-explorer, kb-architect | Codebase exploration, KB creation |
| **Dev** | prompt-crafter, dev-loop-executor | Dev Loop workflow |

### Agent Reference Syntax

In PROMPT.md files, reference agents with `@agent-name`:

```markdown
### CORE
- [ ] @kb-architect: Create Redis KB domain
- [ ] @python-developer: Implement cache wrapper
- [ ] @test-generator: Add unit tests
```

---

## Coding Standards

### Language: Python 3.11+

- **Style:** Ruff (line-length 100, select E/F/I/UP/B/SIM)
- **Testing:** pytest with -v --tb=short
- **Validation:** Pydantic v2 for all data models
- **Package Management:** pyproject.toml with hatchling
- **Type Hints:** Required on all function signatures

### Detected Patterns

| Pattern | Count | Example Files |
| ------- | ----- | ------------- |
| Pydantic Models | 20 | `functions/gcp/v1/src/shared/schemas/invoice.py`, `src/invoice_extractor/models.py` |
| Dataclasses | 20 | `functions/gcp/v1/src/shared/adapters/observability.py`, `tests/smoke/runner.py` |
| Adapter Pattern | 5 | `shared/adapters/storage.py`, `messaging.py`, `bigquery.py`, `llm.py`, `observability.py` |
| Functions Framework | 5 | All `main.py` in Cloud Run functions |
| Computed Fields | 15 | `LineItem.amount`, `ExtractedInvoice.line_item_count`, `gen/schemas/invoice.py` |
| Model Validators | 7 | `ExtractedInvoice.validate_dates()`, `validate_line_items_total()` |
| Test Functions | 204 | Across 14 test files in `tests/`, `functions/gcp/v1/tests/`, `gen/tests/` |

### Code Quality Rules

1. **Pydantic for schemas** - All extraction outputs must use Pydantic models
2. **Type hints required** - All function signatures must be typed
3. **Structured logging** - Use structured JSON logging in Cloud Run
4. **Adapter interfaces** - Use adapters for cloud services (future portability)
5. **Computed fields** - Use `@computed_field` for derived values
6. **Model validators** - Use `@model_validator` for cross-field validation

---

## Commands

| Command | Purpose |
| ------- | ------- |
| `/brainstorm` | Explore ideas through collaborative dialogue |
| `/define` | Capture and validate requirements |
| `/design` | Create technical architecture |
| `/build` | Execute implementation |
| `/ship` | Archive completed features |
| `/iterate` | Update documents mid-stream |
| `/dev` | Dev Loop for structured iteration |
| `/create-kb` | Create knowledge base domains |
| `/review` | Code review workflow |
| `/create-pr` | Create pull requests |
| `/memory` | Save session insights |
| `/sync-context` | Update CLAUDE.md with project context |
| `/readme-maker` | Generate comprehensive README |

---

## Knowledge Base

8 MCP-validated domains with concepts, patterns, and quick references:

| Domain | Purpose | Entry Point |
| ------ | ------- | ----------- |
| **pydantic** | Data validation for LLM output parsing | `.claude/kb/pydantic/index.md` |
| **gcp** | GCP serverless data engineering | `.claude/kb/gcp/index.md` |
| **gemini** | Gemini multimodal LLM for document extraction | `.claude/kb/gemini/index.md` |
| **langfuse** | LLMOps observability platform | `.claude/kb/langfuse/index.md` |
| **terraform** | Infrastructure as Code for GCP | `.claude/kb/terraform/index.md` |
| **terragrunt** | Multi-environment orchestration | `.claude/kb/terragrunt/index.md` |
| **crewai** | Multi-agent AI orchestration | `.claude/kb/crewai/index.md` |
| **openrouter** | Unified LLM API gateway | `.claude/kb/openrouter/index.md` |

### KB Structure

```text
.claude/kb/{domain}/
├── index.md           # Domain overview
├── quick-reference.md # Cheat sheet
├── concepts/          # Core concepts
├── patterns/          # Implementation patterns
└── specs/             # YAML specifications (optional)
```

---

## Infrastructure (Terraform + Terragrunt)

### Terraform Modules

| Module | Resources | Purpose |
| ------ | --------- | ------- |
| `bigquery` | Dataset, tables | Invoice data storage |
| `cloud-run` | Functions, triggers | Serverless compute |
| `gcs` | Buckets | File storage (input, processed, archive) |
| `iam` | Service accounts, roles | Least-privilege access |
| `pubsub` | Topics, subscriptions, DLQ | Event messaging |
| `secrets` | Secret Manager | API keys, credentials |

### Terragrunt Environments

```text
infra/environments/
└── prod/
    ├── bigquery/terragrunt.hcl
    ├── cloud-run/terragrunt.hcl
    ├── gcs/terragrunt.hcl
    ├── iam/terragrunt.hcl
    ├── pubsub/terragrunt.hcl
    └── secrets/terragrunt.hcl
```

---

## CI/CD Pipelines

| Workflow | Trigger | Purpose |
| -------- | ------- | ------- |
| `ci.yaml` | Push/PR | Lint, test, and validate code changes |
| `cd-dev.yaml` | Push to develop | Deploy to development environment |
| `cd-prod.yaml` | Push to main | Deploy to production environment |
| `terraform.yaml` | Changes to infra/ | Terraform plan and apply |
| `smoke-tests.yaml` | Post-deploy | End-to-end pipeline validation |
| `claude-review.yaml` | PR | AI-powered code review with Claude |

---

## MCP Tools Available

| MCP Server | Purpose |
| ---------- | ------- |
| **context7-mcp** | Library documentation lookup |
| **exa** | Code context search |
| **firecrawl** | Web scraping and crawling |
| **magic** | UI component generation |
| **ref-tools** | Documentation search |

---

## Environment Configuration

### Required Environment Variables

| Variable | Purpose |
| -------- | ------- |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `GCP_REGION` | GCP region (us-central1) |
| `LANGFUSE_PUBLIC_KEY` | LangFuse observability |
| `LANGFUSE_SECRET_KEY` | LangFuse secret |
| `OPENROUTER_API_KEY` | Fallback LLM provider |

### GCP Projects

| Environment | Project | Purpose |
| ----------- | ------- | ------- |
| dev | `invoice-pipeline-dev` | Development and testing |
| prod | `invoice-pipeline-prod` | Production workloads |

---

## Important Dates

| Date | Milestone |
| ---- | --------- |
| Jan 15, 2026 | Project kickoff |
| Jan 30, 2026 | Invoice Pipeline shipped |
| Jan 31, 2026 | GCS Upload, LangFuse, Smoke Test, Terraform shipped |
| Feb 7, 2026 | All 5 functions implemented |
| Feb 28, 2026 | MVP demo to stakeholders |
| Mar 15, 2026 | Accuracy validation complete |
| **Apr 1, 2026** | **Production launch** |
| Apr 30, 2026 | CrewAI pilot complete |

---

## Success Metrics

| Metric | Target |
| ------ | ------ |
| Extraction accuracy | ≥ 90% |
| Processing latency P95 | < 30 seconds |
| Pipeline availability | > 99% |
| Cost per invoice | < $0.01 |
| Manual processing reduction | > 80% |

---

## Getting Help

- **Requirements:** Start with [notes/summary-requirements.md](notes/summary-requirements.md)
- **Architecture:** See [.claude/sdd/architecture/ARCHITECTURE.md](.claude/sdd/architecture/ARCHITECTURE.md)
- **Cloud Run Design:** See [design/gcp-cloud-run-fncs.md](design/gcp-cloud-run-fncs.md)
- **Invoice Extractor:** See [design/invoice-extractor-design.md](design/invoice-extractor-design.md)
- **Infrastructure:** See [design/infra-terraform-terragrunt-design.md](design/infra-terraform-terragrunt-design.md)
- **SDD Workflow:** See [.claude/sdd/_index.md](.claude/sdd/_index.md)
- **SDD Examples:** See [.claude/sdd/examples/](.claude/sdd/examples/)
- **Dev Loop:** See [.claude/dev/_index.md](.claude/dev/_index.md)
- **Dev Examples:** See [.claude/dev/examples/](.claude/dev/examples/)
- **Agents:** Browse [.claude/agents/](.claude/agents/)
- **KB Index:** See [.claude/kb/_index.yaml](.claude/kb/_index.yaml)

---

## Version History

| Date | Changes |
| ---- | ------- |
| 2026-01-31 | Sync: Added Active Features section with PIPELINE_OBSERVABILITY_METRICS; added timing.py utility to Shared Components; updated test count (196 → 204 tests across 14 files) |
| 2026-01-31 | Sync: Updated pattern counts (Pydantic: 20, Dataclasses: 20, Computed Fields: 15, Model Validators: 7); added 196 test functions; added CI/CD Pipelines section with 6 GitHub Actions workflows |
| 2026-01-31 | Sync: Added functions/gcp/v1/ with 5 Cloud Run functions, infra/ with Terraform modules, tests/smoke/, src/invoice_extractor/; updated shipped features (5); added /readme-maker command |
| 2026-01-29 | Sync: Added design/, archive/, examples folders; updated agent counts per category |
| 2026-01-29 | Initial CLAUDE.md created via /sync-context |
