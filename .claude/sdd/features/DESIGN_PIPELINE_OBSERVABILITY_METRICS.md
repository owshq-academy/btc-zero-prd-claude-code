# DESIGN: Pipeline Observability Metrics

> Technical design for adding latency timing and file size metrics to all four pipeline functions

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | PIPELINE_OBSERVABILITY_METRICS |
| **Date** | 2026-01-31 |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_PIPELINE_OBSERVABILITY_METRICS.md](./DEFINE_PIPELINE_OBSERVABILITY_METRICS.md) |
| **Status** | Ready for Build |

---

## Architecture Overview

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY METRICS INJECTION                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐  │
│  │ tiff_to_png │   │  classifier │   │  extractor  │   │ bq_writer   │  │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘  │
│         │                 │                 │                 │          │
│    ┌────▼────┐       ┌────▼────┐       ┌────▼────┐       ┌────▼────┐    │
│    │ START   │       │ START   │       │ START   │       │ START   │    │
│    │ TIMER   │       │ TIMER   │       │ TIMER   │       │ TIMER   │    │
│    └────┬────┘       └────┬────┘       └────┬────┘       └────┬────┘    │
│         │                 │                 │                 │          │
│    ┌────▼────┐       ┌────▼────┐       ┌────▼────┐            │          │
│    │ READ    │       │ READ    │       │ READ    │            │          │
│    │ + SIZE  │       │ + SIZE  │       │ + SIZE  │       (no file)      │
│    └────┬────┘       └────┬────┘       └────┬────┘            │          │
│         │                 │                 │                 │          │
│    ┌────▼────┐            │                 │                 │          │
│    │ WRITE   │       (no write)        (no write)             │          │
│    │ + SIZE  │            │                 │                 │          │
│    └────┬────┘            │                 │                 │          │
│         │                 │                 │                 │          │
│    ┌────▼────┐       ┌────▼────┐       ┌────▼────┐       ┌────▼────┐    │
│    │ END     │       │ END     │       │ END     │       │ END     │    │
│    │ TIMER   │       │ TIMER   │       │ TIMER   │       │ TIMER   │    │
│    └────┬────┘       └────┬────┘       └────┬────┘       └────┬────┘    │
│         │                 │                 │                 │          │
│         ▼                 ▼                 ▼                 ▼          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     STRUCTURED LOG OUTPUT                        │    │
│  │  {"latency_ms": 1234, "input_size_bytes": 56789, ...}          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│                                    ▼                                     │
│                            Cloud Logging                                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| `timing.py` | Shared timing context manager and utilities | Python `time.perf_counter()` |
| `tiff_to_png/main.py` | Add latency + input/output sizes | Python logging `extra={}` |
| `invoice_classifier/main.py` | Add latency + input sizes | Python logging `extra={}` |
| `data_extractor/main.py` | Add function latency (distinct from LLM latency) | Python logging `extra={}` |
| `bigquery_writer/main.py` | Add latency | Python logging `extra={}` |

---

## Key Decisions

### Decision 1: Add Shared Timing Utility vs Inline Code

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-31 |

**Context:** Each function needs timing code. We could either add inline `time.perf_counter()` calls to each function, or create a reusable utility in `shared/utils/`.

**Choice:** Create a `FunctionTimer` context manager in `shared/utils/timing.py`

**Rationale:**
- Eliminates copy-paste errors in timing calculation
- Provides consistent `latency_ms` field naming
- Context manager pattern ensures timing captures the full scope including exceptions
- Already have precedent: `shared/utils/` contains `logging.py`, `config.py`, `gcs.py`

**Alternatives Rejected:**
1. Inline timing in each function - Rejected because of code duplication and risk of inconsistent field names
2. Decorator pattern - Rejected because we need access to timing value inside the function for intermediate logs

**Consequences:**
- Adds 1 new file to shared utilities
- Requires import in each function
- Slight learning curve for new contributors

---

### Decision 2: Field Naming Convention

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-31 |

**Context:** Need consistent field names across all functions for Cloud Logging queries.

**Choice:** Use snake_case with `_ms` and `_bytes` suffixes:
- `latency_ms` - Total function execution time
- `input_size_bytes` - Single file input size
- `total_input_bytes` - Sum of multiple file sizes
- `output_size_bytes` - Single file output size
- `total_output_bytes` - Sum of multiple output file sizes

**Rationale:**
- Matches existing patterns in codebase (`size_bytes`, `extraction_latency_ms`)
- Snake_case is Python convention and consistent with Cloud Logging
- Explicit `_ms` and `_bytes` suffixes prevent ambiguity

**Alternatives Rejected:**
1. `latency` without unit - Rejected because ambiguous (seconds vs milliseconds)
2. `file_size` without `input/output` - Rejected because doesn't distinguish reads from writes

**Consequences:**
- Clear, queryable field names in Cloud Logging
- Easy to build log-based metrics

---

### Decision 3: Timer Scope - Full Function vs Partial

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-31 |

**Context:** Should timing capture the entire function execution or just specific operations?

**Choice:** Capture full function execution time from entry to exit/exception

**Rationale:**
- Matches what DevOps cares about: "how long did this function take?"
- Already have granular metrics: LLM latency in `data_extractor`, GCS operation logs
- Simple to implement with context manager
- Captures setup and teardown time that matters for cost

**Alternatives Rejected:**
1. Multiple fine-grained timers - Rejected because adds complexity without clear benefit (we have LangFuse for LLM granularity)

**Consequences:**
- Single `latency_ms` field per function invocation
- Easy to aggregate and alert on

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `functions/gcp/v1/src/shared/utils/timing.py` | Create | FunctionTimer context manager | @function-developer | None |
| 2 | `functions/gcp/v1/src/shared/utils/__init__.py` | Modify | Export FunctionTimer | @function-developer | 1 |
| 3 | `functions/gcp/v1/src/functions/tiff_to_png/main.py` | Modify | Add latency + file sizes | @function-developer | 1 |
| 4 | `functions/gcp/v1/src/functions/invoice_classifier/main.py` | Modify | Add latency + file sizes | @function-developer | 1 |
| 5 | `functions/gcp/v1/src/functions/data_extractor/main.py` | Modify | Add function latency | @function-developer | 1 |
| 6 | `functions/gcp/v1/src/functions/bigquery_writer/main.py` | Modify | Add latency | @function-developer | 1 |
| 7 | `functions/gcp/v1/tests/test_timing.py` | Create | Unit tests for timing utility | @test-generator | 1 |

**Total Files:** 7

---

## Agent Assignment Rationale

> Agents discovered from `.claude/agents/` - Build phase invokes matched specialists.

| Agent | Files Assigned | Why This Agent |
|-------|----------------|----------------|
| @function-developer | 1, 2, 3, 4, 5, 6 | Cloud Run function code specialist |
| @test-generator | 7 | pytest unit test specialist |

**Agent Discovery:**
- Scanned: `.claude/agents/**/*.md`
- Matched by: File type (Python), purpose (Cloud Run functions), path patterns (`functions/gcp/`)

---

## Code Patterns

### Pattern 1: FunctionTimer Context Manager

```python
# shared/utils/timing.py
"""Function timing utilities for observability."""

import time
from contextlib import contextmanager
from typing import Generator


@contextmanager
def function_timer() -> Generator[dict[str, int], None, None]:
    """Context manager for measuring function execution time.

    Yields a mutable dict that will contain 'latency_ms' after the context exits.
    The dict can be included in log extra fields.

    Example:
        with function_timer() as timing:
            # ... do work ...

        logger.info("Complete", extra={"latency_ms": timing["latency_ms"]})

    Yields:
        Dict with 'latency_ms' key (populated on exit)
    """
    metrics: dict[str, int] = {}
    start = time.perf_counter()
    try:
        yield metrics
    finally:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        metrics["latency_ms"] = elapsed_ms
```

### Pattern 2: Function Entry Point with Timing

```python
# Example usage in main.py
from shared.utils import function_timer

@functions_framework.cloud_event
def handle_invoice(cloud_event: CloudEvent) -> None:
    """Cloud Run entry point."""
    with function_timer() as timing:
        # ... existing function logic ...

        logger.info(
            "Processing complete",
            extra={
                "latency_ms": timing["latency_ms"],
                "input_size_bytes": len(file_data),
                # ... other fields ...
            },
        )
```

### Pattern 3: File Size Tracking

```python
# For single file operations
tiff_data = storage.read(bucket, file_path)
input_size_bytes = len(tiff_data)

logger.info(
    "Downloaded file",
    extra={
        "file_path": file_path,
        "input_size_bytes": input_size_bytes,
    },
)

# For multiple files
total_input_bytes = 0
for png_uri in message.converted_files:
    bucket, path = parse_gcs_uri(png_uri)
    png_data = storage.read(bucket, path)
    total_input_bytes += len(png_data)
    images_data.append(png_data)

logger.info(
    "Downloaded all images",
    extra={
        "file_count": len(images_data),
        "total_input_bytes": total_input_bytes,
    },
)
```

### Pattern 4: Output Size Tracking (tiff_to_png)

```python
# Track output sizes when writing multiple files
total_output_bytes = 0
for i, png_data in enumerate(result.pages):
    png_path = f"{base_name}_page{i + 1}.png"
    uri = storage.write(config.processed_bucket, png_path, png_data, "image/png")
    total_output_bytes += len(png_data)

logger.info(
    "Conversion complete",
    extra={
        "latency_ms": timing["latency_ms"],
        "input_size_bytes": len(tiff_data),
        "total_output_bytes": total_output_bytes,
        "page_count": result.page_count,
    },
)
```

---

## Data Flow

```text
1. Cloud Event triggers function entry
   │
   ▼
2. FunctionTimer context manager starts (captures start time)
   │
   ▼
3. Function reads files from GCS → track input_size_bytes
   │
   ▼
4. Function processes data (conversion, classification, extraction, write)
   │
   ▼
5. Function writes files (if applicable) → track output_size_bytes
   │
   ▼
6. FunctionTimer calculates latency_ms on context exit
   │
   ▼
7. Final log entry includes all metrics
   │
   ▼
8. Cloud Logging receives structured JSON with metrics
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|-----------------|----------------|
| Cloud Logging | Structured JSON logs via stdout | None (automatic) |
| Cloud Monitoring | Log-based metrics (future) | None (automatic) |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|---------------|
| Unit | FunctionTimer | `test_timing.py` | pytest | 100% |
| Integration | Full function execution | Existing smoke tests | pytest | Verify logs contain metrics |

### Unit Test Cases

```python
# test_timing.py
def test_function_timer_returns_positive_latency():
    """Timer should return positive milliseconds."""
    with function_timer() as timing:
        time.sleep(0.01)  # 10ms

    assert "latency_ms" in timing
    assert timing["latency_ms"] >= 10

def test_function_timer_captures_exception_time():
    """Timer should still capture time even on exception."""
    try:
        with function_timer() as timing:
            time.sleep(0.005)
            raise ValueError("test error")
    except ValueError:
        pass

    assert timing["latency_ms"] >= 5

def test_function_timer_millisecond_precision():
    """Timer should be in milliseconds (int)."""
    with function_timer() as timing:
        pass

    assert isinstance(timing["latency_ms"], int)
```

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|-------------------|--------|
| Timing exception | Context manager's `finally` ensures timing is captured | N/A |
| GCS read failure | Existing error handling unchanged | Yes (via Pub/Sub) |
| Log write failure | Non-blocking (stdout to Cloud Logging) | No |

---

## Configuration

No configuration changes required. Timing utility uses standard library only.

---

## Security Considerations

- No sensitive data in timing metrics
- File sizes are metadata only, not file contents
- No new authentication or authorization required

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| Logging | Enhanced: `latency_ms`, `input_size_bytes`, `output_size_bytes` fields |
| Metrics | Can create log-based metrics in Cloud Monitoring (out of scope) |
| Tracing | Unchanged (LangFuse handles LLM tracing) |

### Example Cloud Logging Queries

```sql
-- Find slow functions (>5 seconds)
resource.type="cloud_run_revision"
jsonPayload.latency_ms > 5000

-- Analyze file sizes by function
resource.type="cloud_run_revision"
jsonPayload.input_size_bytes > 0

-- Correlation: latency vs file size
resource.type="cloud_run_revision"
jsonPayload.latency_ms > 0
jsonPayload.input_size_bytes > 0
```

---

## Implementation Order

Build phase should implement in this order:

1. **Create `timing.py`** - Foundation utility
2. **Update `__init__.py`** - Export the utility
3. **Modify `tiff_to_png/main.py`** - Most metrics (input + output sizes)
4. **Modify `invoice_classifier/main.py`** - Input sizes
5. **Modify `data_extractor/main.py`** - Function vs LLM latency distinction
6. **Modify `bigquery_writer/main.py`** - Latency only
7. **Create `test_timing.py`** - Verify timing utility

---

## Acceptance Criteria Mapping

| DEFINE AT-ID | DESIGN Implementation |
|--------------|----------------------|
| AT-001 | `tiff_to_png` completion log includes `latency_ms` |
| AT-002 | `tiff_to_png` logs include `input_size_bytes`, `total_output_bytes` |
| AT-003 | `invoice_classifier` completion log includes `latency_ms` |
| AT-004 | `invoice_classifier` logs `total_input_bytes` after downloading PNGs |
| AT-005 | `data_extractor` logs function-level `latency_ms` in completion message |
| AT-006 | `bigquery_writer` completion log includes `latency_ms` |
| AT-007 | All metrics use `extra={}` dict → JSON fields in Cloud Logging |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-31 | design-agent | Initial version |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_PIPELINE_OBSERVABILITY_METRICS.md`
