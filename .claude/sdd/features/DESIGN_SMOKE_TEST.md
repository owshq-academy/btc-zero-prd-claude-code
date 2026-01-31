# DESIGN: Smoke Test Framework

> Technical design for implementing end-to-end pipeline validation CLI

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | SMOKE_TEST |
| **Date** | 2026-01-30 |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_SMOKE_TEST.md](./DEFINE_SMOKE_TEST.md) |
| **Status** | Ready for Build |

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SMOKE TEST CLI ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  CLI ENTRY POINT                                                                │
│  ────────────────                                                                │
│                                                                                  │
│  $ smoke-test run --env dev --vendor ubereats                                   │
│         │                                                                        │
│         ▼                                                                        │
│  ┌─────────────────┐                                                            │
│  │   cli.py        │ ← Click CLI with options: --env, --vendor, --output, etc.  │
│  │   (Click)       │                                                            │
│  └────────┬────────┘                                                            │
│           │                                                                      │
│           ▼                                                                      │
│  STAGE ORCHESTRATOR                                                             │
│  ──────────────────                                                              │
│                                                                                  │
│  ┌─────────────────┐                                                            │
│  │   runner.py     │ ← Executes stages sequentially, fail-fast on error        │
│  │   (Orchestrator)│                                                            │
│  └────────┬────────┘                                                            │
│           │                                                                      │
│           ▼                                                                      │
│  STAGES (Pipeline)                                                              │
│  ─────────────────                                                               │
│                                                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │GENERATE │─▶│ UPLOAD  │─▶│ PROCESS │─▶│VALIDATE │─▶│BIGQUERY │─▶│ LOGGING │ │
│  │Stage 1  │  │Stage 2  │  │Stage 3  │  │Stage 4  │  │Stage 5  │  │Stage 6  │ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │
│       │           │           │             │             │           │         │
│       ▼           ▼           ▼             ▼             ▼           ▼         │
│  invoice-gen    GCS API    GCS Polling   Field Match   BQ Query   Cloud Logs   │
│                                                                                  │
│  EXTERNAL SYSTEMS                                                               │
│  ────────────────                                                                │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          GCP Infrastructure                              │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐    │   │
│  │  │   GCS     │  │ Cloud Run │  │ BigQuery  │  │  Cloud Logging    │    │   │
│  │  │ Bucket    │  │ Functions │  │  Table    │  │                   │    │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────────────┘    │   │
│  │                                                                          │   │
│  │  Bucket: eda-gemini-{env}-pipeline                                      │   │
│  │  Dataset: ds_bq_gemini_{env}                                            │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  OUTPUT                                                                         │
│  ──────                                                                          │
│                                                                                  │
│  ┌─────────────────┐                                                            │
│  │ SmokeResult     │ ← JSON with stage results, timing, pass/fail              │
│  │ (Pydantic)      │                                                            │
│  └─────────────────┘                                                            │
│         │                                                                        │
│         ▼                                                                        │
│  stdout: Summary     results.json: Full report     Exit code: 0 or 1           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **cli.py** | CLI entry point with Click | Click 8.x |
| **runner.py** | Stage orchestrator with fail-fast | Python stdlib |
| **stages/** | Individual stage implementations | Python + GCP SDKs |
| **validators/** | Field matching and comparison | Pydantic + custom |
| **models.py** | Result models (SmokeResult, StageResult) | Pydantic 2.x |
| **config.py** | Configuration loader | PyYAML + Pydantic |

---

## Key Decisions

### Decision 1: Stage Interface Pattern

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** Need consistent interface for all 6 stages to enable orchestration and fail-fast behavior.

**Choice:** Abstract base class `Stage` with `run(context) -> StageResult` method. Each stage receives previous stage's output via `SmokeContext` dataclass.

**Rationale:**
- Single interface simplifies orchestrator
- Context passing enables stage chaining
- StageResult captures pass/fail, timing, and errors consistently

**Alternatives Rejected:**
1. Function-based stages - No type hints for inputs/outputs, harder to test
2. Protocol-based stages - ABC is simpler and more explicit for 6 concrete stages

**Consequences:**
- All stages must inherit from Stage ABC
- Context grows as stages execute (contains all intermediate data)

---

### Decision 2: Ground Truth from invoice-gen

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** Need known-correct values to compare extraction output against.

**Choice:** Use `GeneratedInvoice.invoice_data` from invoice-gen as ground truth. The generator already returns a Pydantic model with all expected values.

**Rationale:**
- No separate fixture files needed
- Ground truth is generated atomically with TIFF
- InvoiceData schema matches extraction schema closely

**Alternatives Rejected:**
1. JSON sidecar files - Extra file management, can drift from TIFF
2. Hardcoded fixtures - Not realistic, limited vendor coverage

**Consequences:**
- Smoke test depends on invoice-gen package
- Field mapping needed between InvoiceData → ExtractedInvoice schemas

---

### Decision 3: GCS Polling Strategy

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** Pipeline is event-driven (Pub/Sub), but smoke test runner is synchronous CLI.

**Choice:** Poll GCS `extracted/{vendor}/` folder every 2 seconds for up to 60 seconds. Check for JSON file with matching invoice_id.

**Rationale:**
- Simple to implement
- 60s timeout matches P95 latency target (30s) with buffer
- 2s interval balances responsiveness vs API calls

**Alternatives Rejected:**
1. Subscribe to Pub/Sub - Adds infrastructure complexity for CLI tool
2. One-shot check - Would miss async pipeline completion

**Consequences:**
- Billable GCS API calls during polling (minimal cost)
- Timeout parameter should be configurable

---

### Decision 4: Field Matcher Strategy

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** Need to compare extracted values against ground truth with different rules per field.

**Choice:** Two-tier matching:
- **Critical fields** (invoice_id, vendor_type, total_amount, currency): Exact match required
- **Other fields**: Schema validation only (Pydantic parses successfully)

**Rationale:**
- Critical fields drive business accuracy (90% target)
- Over-strict matching on addresses, names would cause false failures
- Matches DEFINE requirements

**Alternatives Rejected:**
1. Fuzzy matching everywhere - Hard to define thresholds, unclear failures
2. All exact match - Too strict for addresses, phone numbers

**Consequences:**
- FieldMatcher class needs configurable critical field list
- Validation failures clearly indicate which field mismatched

---

### Decision 5: Reuse invoice-gen as Library

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** Smoke test needs to generate invoices. invoice-gen already exists.

**Choice:** Import `InvoiceGenerator` from `invoice_gen` package directly. Add invoice_gen as dependency to smoke test pyproject.toml.

**Rationale:**
- DRY - don't duplicate generation logic
- Generator is already tested and working
- Same codebase, easy to import

**Alternatives Rejected:**
1. Shell out to invoice-gen CLI - Parse stdout, handle errors, less control
2. Copy generator code - Duplication, drift risk

**Consequences:**
- Smoke test has dependency on invoice_gen
- Must use compatible Python version and dependencies

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `tests/smoke/__init__.py` | Create | Package init | (general) | None |
| 2 | `tests/smoke/models.py` | Create | Pydantic models: SmokeResult, StageResult, SmokeContext | @python-developer | None |
| 3 | `tests/smoke/config.py` | Create | Configuration loader + SmokeConfig model | @python-developer | None |
| 4 | `tests/smoke/config/smoke_config.yaml` | Create | Default configuration (timeouts, thresholds) | (general) | None |
| 5 | `tests/smoke/stages/__init__.py` | Create | Stage exports | (general) | None |
| 6 | `tests/smoke/stages/base.py` | Create | Stage ABC and StageResult | @python-developer | 2 |
| 7 | `tests/smoke/stages/generate.py` | Create | Stage 1: Generate invoice via invoice-gen | @python-developer | 2, 6 |
| 8 | `tests/smoke/stages/upload.py` | Create | Stage 2: Upload TIFF to GCS | @python-developer | 2, 6 |
| 9 | `tests/smoke/stages/process.py` | Create | Stage 3: Poll for extraction completion | @python-developer | 2, 6 |
| 10 | `tests/smoke/stages/validate.py` | Create | Stage 4: Compare extraction vs ground truth | @python-developer | 2, 6, 11 |
| 11 | `tests/smoke/validators/__init__.py` | Create | Validator exports | (general) | None |
| 12 | `tests/smoke/validators/field_matcher.py` | Create | Critical field exact match + comparison | @python-developer | 2 |
| 13 | `tests/smoke/stages/bigquery.py` | Create | Stage 5: Query BQ for row | @python-developer | 2, 6 |
| 14 | `tests/smoke/stages/logging.py` | Create | Stage 6: Check Cloud Logging for errors | @python-developer | 2, 6 |
| 15 | `tests/smoke/runner.py` | Create | Stage orchestrator with fail-fast | @python-developer | 2, 5-14 |
| 16 | `tests/smoke/cli.py` | Create | Click CLI entry point | @python-developer | 2, 3, 15 |
| 17 | `tests/smoke/pyproject.toml` | Create | Package config with dependencies | (general) | None |
| 18 | `tests/smoke/fixtures/.gitkeep` | Create | Placeholder for optional fixtures | (general) | None |

**Total Files:** 18

---

## Agent Assignment Rationale

> Agents discovered from `.claude/agents/` - Build phase invokes matched specialists.

| Agent | Files Assigned | Why This Agent |
|-------|----------------|----------------|
| @python-developer | 2, 3, 6-10, 12-16 | Python code architect for data engineering; Pydantic expertise |
| (general) | 1, 4, 5, 11, 17, 18 | Simple files (inits, YAML, gitkeep) - no specialist needed |

**Agent Discovery:**
- Scanned: `.claude/agents/**/*.md`
- Matched by: Python, Pydantic, dataclasses keywords in python-developer agent

---

## Code Patterns

### Pattern 1: Stage Base Class

```python
# tests/smoke/stages/base.py
"""Base class for all smoke test stages."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class StageResult:
    """Result from a single stage execution."""

    stage_name: str
    passed: bool
    duration_ms: int
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage_name,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
            "error": self.error,
            **self.data,
        }


class Stage(ABC):
    """Abstract base class for smoke test stages."""

    name: str  # Override in subclass

    @abstractmethod
    def run(self, context: "SmokeContext") -> StageResult:
        """Execute the stage and return result."""
        pass

    def _timed_run(self, context: "SmokeContext") -> StageResult:
        """Wrapper that adds timing to any stage."""
        start = datetime.now()
        try:
            result = self.run(context)
        except Exception as e:
            duration = int((datetime.now() - start).total_seconds() * 1000)
            return StageResult(
                stage_name=self.name,
                passed=False,
                duration_ms=duration,
                error=str(e),
            )
        result.duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        return result
```

### Pattern 2: Smoke Context (State Passing)

```python
# tests/smoke/models.py
"""Pydantic models for smoke test results and context."""

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


@dataclass
class SmokeContext:
    """Mutable context passed between stages."""

    # Configuration
    env: str = "dev"
    vendor: str = "ubereats"

    # Stage 1 outputs
    invoice_data: Any = None  # InvoiceData from invoice-gen (ground truth)
    tiff_path: Path | None = None

    # Stage 2 outputs
    gcs_object_path: str | None = None

    # Stage 3 outputs
    extracted_json_path: str | None = None
    extracted_data: dict | None = None

    # Stage 4 outputs
    validation_passed: bool = False
    field_mismatches: list[str] = field(default_factory=list)

    # Stage 5 outputs
    bq_row_found: bool = False

    # Stage 6 outputs
    log_errors_found: list[str] = field(default_factory=list)


class SmokeResult(BaseModel):
    """Final smoke test result with all stage outcomes."""

    success: bool = Field(description="True if all stages passed")
    env: str = Field(description="Environment tested (dev/prod)")
    vendor: str = Field(description="Vendor type tested")
    total_duration_ms: int = Field(description="Total test duration in ms")
    stages: list[dict] = Field(default_factory=list, description="Per-stage results")

    # Summary
    stages_passed: int = Field(default=0)
    stages_failed: int = Field(default=0)
    stages_skipped: int = Field(default=0)

    # Details for debugging
    invoice_id: str | None = Field(default=None)
    error_summary: str | None = Field(default=None)
```

### Pattern 3: Generate Stage (using invoice-gen)

```python
# tests/smoke/stages/generate.py
"""Stage 1: Generate synthetic invoice with ground truth."""

from pathlib import Path
import tempfile

from invoice_gen.generator import InvoiceGenerator
from invoice_gen.schemas.invoice import VendorType

from tests.smoke.stages.base import Stage, StageResult
from tests.smoke.models import SmokeContext


class GenerateStage(Stage):
    """Generate a synthetic invoice using invoice-gen."""

    name = "generate"

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or Path(tempfile.mkdtemp())

    def run(self, context: SmokeContext) -> StageResult:
        vendor_type = VendorType(context.vendor)

        generator = InvoiceGenerator(
            output_dir=self.output_dir,
            keep_intermediates=False,
        )

        result = generator.generate_tiff(vendor_type)

        # Store in context for next stages
        context.invoice_data = result.invoice_data  # Ground truth!
        context.tiff_path = result.tiff_path

        return StageResult(
            stage_name=self.name,
            passed=True,
            duration_ms=0,  # Set by _timed_run
            data={
                "invoice_id": result.invoice_data.invoice_id,
                "tiff_path": str(result.tiff_path),
                "vendor": vendor_type.value,
            },
        )
```

### Pattern 4: Field Matcher (Critical vs Optional)

```python
# tests/smoke/validators/field_matcher.py
"""Field matching for extraction validation."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class FieldMatch:
    """Result of comparing a single field."""
    field_name: str
    expected: Any
    actual: Any
    matched: bool
    is_critical: bool


CRITICAL_FIELDS = {"invoice_id", "vendor_type", "total_amount", "currency"}


def match_fields(
    expected: dict,
    actual: dict,
    critical_fields: set[str] | None = None,
) -> tuple[bool, list[FieldMatch]]:
    """Compare expected vs actual with critical field enforcement.

    Returns:
        Tuple of (all_critical_passed, list of FieldMatch results)
    """
    critical = critical_fields or CRITICAL_FIELDS
    results: list[FieldMatch] = []

    for field_name in critical:
        exp_val = expected.get(field_name)
        act_val = actual.get(field_name)

        # Handle Decimal comparison
        if isinstance(exp_val, Decimal):
            exp_val = float(exp_val)
        if isinstance(act_val, (Decimal, str)):
            try:
                act_val = float(act_val)
            except (ValueError, TypeError):
                pass

        matched = exp_val == act_val
        results.append(FieldMatch(
            field_name=field_name,
            expected=exp_val,
            actual=act_val,
            matched=matched,
            is_critical=True,
        ))

    all_critical_passed = all(r.matched for r in results if r.is_critical)
    return all_critical_passed, results
```

### Pattern 5: Configuration Structure

```yaml
# tests/smoke/config/smoke_config.yaml
# Smoke Test Configuration

environments:
  dev:
    project: eda-gemini-dev
    bucket: eda-gemini-dev-pipeline
    dataset: ds_bq_gemini_dev
    region: us-central1

  prod:
    project: eda-gemini-prd
    bucket: eda-gemini-prd-pipeline
    dataset: ds_bq_gemini_prd
    region: us-central1

stages:
  generate:
    timeout_seconds: 30

  upload:
    timeout_seconds: 10
    folder: landing

  process:
    timeout_seconds: 60
    poll_interval_seconds: 2
    folders_to_check:
      - converted
      - classified
      - extracted

  validate:
    timeout_seconds: 10
    critical_fields:
      - invoice_id
      - vendor_type
      - total_amount
      - currency

  bigquery:
    timeout_seconds: 15
    table: extractions

  logging:
    timeout_seconds: 10
    lookback_minutes: 5
    severity_threshold: ERROR

vendors:
  ubereats:
    invoice_id_pattern: "INV-UE-*"
  doordash:
    invoice_id_pattern: "INV-DD-*"
  grubhub:
    invoice_id_pattern: "INV-GH-*"
```

### Pattern 6: CLI Entry Point

```python
# tests/smoke/cli.py
"""Click CLI for smoke test execution."""

import json
import sys
from pathlib import Path

import click

from tests.smoke.config import load_config
from tests.smoke.models import SmokeContext, SmokeResult
from tests.smoke.runner import SmokeRunner


@click.command()
@click.option(
    "--env",
    type=click.Choice(["dev", "prod"]),
    default="dev",
    help="Target environment",
)
@click.option(
    "--vendor",
    type=click.Choice(["ubereats", "doordash", "grubhub", "ifood", "rappi"]),
    default="ubereats",
    help="Vendor type to test",
)
@click.option(
    "--invoice",
    type=click.Path(exists=True),
    default=None,
    help="Use existing TIFF instead of generating",
)
@click.option(
    "--skip-stage",
    multiple=True,
    type=click.Choice(["generate", "upload", "process", "validate", "bigquery", "logging"]),
    help="Skip specific stage(s)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Write JSON results to file",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def run(
    env: str,
    vendor: str,
    invoice: str | None,
    skip_stage: tuple[str, ...],
    output: str | None,
    verbose: bool,
) -> None:
    """Run end-to-end smoke test for invoice pipeline."""

    click.echo(click.style("🔬 Smoke Test Starting", fg="cyan", bold=True))
    click.echo(f"   Environment: {env}")
    click.echo(f"   Vendor: {vendor}")

    if invoice:
        click.echo(f"   Invoice: {invoice}")
    if skip_stage:
        click.echo(f"   Skipping: {', '.join(skip_stage)}")

    click.echo()

    config = load_config(env)
    context = SmokeContext(env=env, vendor=vendor)

    if invoice:
        context.tiff_path = Path(invoice)

    runner = SmokeRunner(
        config=config,
        skip_stages=set(skip_stage),
        verbose=verbose,
    )

    result = runner.run(context)

    # Output
    if output:
        Path(output).write_text(result.model_dump_json(indent=2))
        click.echo(f"📄 Results written to: {output}")

    # Summary
    click.echo()
    if result.success:
        click.echo(click.style("✅ SMOKE TEST PASSED", fg="green", bold=True))
    else:
        click.echo(click.style("❌ SMOKE TEST FAILED", fg="red", bold=True))
        if result.error_summary:
            click.echo(f"   Error: {result.error_summary}")

    click.echo(f"   Duration: {result.total_duration_ms}ms")
    click.echo(f"   Stages: {result.stages_passed} passed, {result.stages_failed} failed, {result.stages_skipped} skipped")

    sys.exit(0 if result.success else 1)


@click.group()
def main():
    """Smoke test CLI for invoice processing pipeline."""
    pass


main.add_command(run)


if __name__ == "__main__":
    main()
```

---

## Data Flow

```text
1. CLI receives arguments (--env dev --vendor ubereats)
   │
   ▼
2. Runner creates SmokeContext with env/vendor
   │
   ▼
3. STAGE 1: GenerateStage
   │  - Calls InvoiceGenerator.generate_tiff(vendor)
   │  - Stores invoice_data (ground truth) + tiff_path in context
   │
   ▼
4. STAGE 2: UploadStage
   │  - Uploads context.tiff_path to GCS landing/
   │  - Stores gcs_object_path in context
   │
   ▼
5. STAGE 3: ProcessStage
   │  - Polls GCS extracted/{vendor}/ for JSON with invoice_id
   │  - Timeout: 60s, poll every 2s
   │  - Stores extracted_json_path + extracted_data in context
   │
   ▼
6. STAGE 4: ValidateStage
   │  - Compares extracted_data vs invoice_data (ground truth)
   │  - Critical fields: exact match required
   │  - Stores validation_passed + field_mismatches in context
   │
   ▼
7. STAGE 5: BigQueryStage
   │  - Queries ds_bq_gemini_{env}.extractions for invoice_id
   │  - Stores bq_row_found in context
   │
   ▼
8. STAGE 6: LoggingStage
   │  - Queries Cloud Logging for ERROR entries with invoice_id
   │  - Stores log_errors_found in context
   │
   ▼
9. Runner aggregates StageResults into SmokeResult
   │  - success = all stages passed
   │  - Calculates total_duration_ms
   │
   ▼
10. CLI outputs summary, writes JSON, returns exit code
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|-----------------|----------------|
| **GCS** | google-cloud-storage SDK | ADC (Application Default Credentials) |
| **BigQuery** | google-cloud-bigquery SDK | ADC |
| **Cloud Logging** | google-cloud-logging SDK | ADC |
| **invoice-gen** | Python import | N/A (local package) |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|---------------|
| Unit | Models, validators, config | `test_models.py`, `test_validators.py` | pytest | 90% of validators |
| Unit | Stage logic (mocked GCP) | `test_stages.py` | pytest + unittest.mock | Each stage |
| Integration | GCS/BQ access (real dev) | `test_integration.py` | pytest + live GCP | Happy path |
| E2E | Full pipeline | Manual | smoke-test CLI | AT-001 to AT-008 |

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|-------------------|--------|
| GCS upload failure | Return StageResult.passed=False with error message | No |
| Polling timeout | Return StageResult.passed=False with timeout error | No |
| Field mismatch | Return StageResult with field_mismatches list | No |
| BQ query failure | Return StageResult.passed=False with error | No |
| Missing credentials | Raise ClickException with setup instructions | No |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `stages.process.timeout_seconds` | int | 60 | Max wait for pipeline processing |
| `stages.process.poll_interval_seconds` | int | 2 | Polling frequency |
| `stages.validate.critical_fields` | list | ["invoice_id", "vendor_type", "total_amount", "currency"] | Fields requiring exact match |
| `stages.logging.lookback_minutes` | int | 5 | Log query time window |

---

## Security Considerations

- **No secrets in config** - Uses ADC for GCP authentication
- **No production data** - Generates synthetic invoices only
- **Read-only BQ access** - Only queries, never writes
- **Scoped logging query** - Filters by invoice_id, not broad access

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| **Logging** | click.echo for user output; structured JSON in --verbose mode |
| **Metrics** | SmokeResult includes duration_ms per stage |
| **Tracing** | Not needed (single CLI execution, not distributed) |

---

## Dependencies (pyproject.toml)

```toml
[project]
name = "smoke-test"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "click>=8.0",
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "google-cloud-storage>=2.0",
    "google-cloud-bigquery>=3.0",
    "google-cloud-logging>=3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov",
]

[project.scripts]
smoke-test = "tests.smoke.cli:main"
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-30 | design-agent | Initial version |

---

## Acceptance Test Mapping

| AT-ID | Covered By | Notes |
|-------|------------|-------|
| AT-001 | runner.py + all stages | Happy path through all 6 stages |
| AT-002 | runner.py fail-fast + upload.py | GCS error handling |
| AT-003 | validate.py + field_matcher.py | Critical field mismatch detection |
| AT-004 | bigquery.py | Row not found handling |
| AT-005 | cli.py --skip-stage | Stage skipping logic |
| AT-006 | cli.py --invoice | Custom invoice input |
| AT-007 | process.py | Timeout handling |
| AT-008 | cli.py --output | JSON file output |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_SMOKE_TEST.md`
