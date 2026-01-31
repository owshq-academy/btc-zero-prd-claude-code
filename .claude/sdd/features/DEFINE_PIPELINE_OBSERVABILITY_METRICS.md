# DEFINE: Pipeline Observability Metrics

> Add latency timing (ms) and file size metrics to structured logs across all four pipeline functions for performance monitoring and troubleshooting.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | PIPELINE_OBSERVABILITY_METRICS |
| **Date** | 2026-01-31 |
| **Author** | define-agent |
| **Status** | Ready for Design |
| **Clarity Score** | 14/15 |

---

## Problem Statement

The invoice processing pipeline lacks consistent latency and file size metrics in structured logs, making it difficult for DevOps engineers and developers to identify performance bottlenecks, monitor processing trends, and troubleshoot slow-running jobs. Currently, only `data_extractor` logs LLM latency, while file sizes are inconsistently tracked.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| DevOps Engineer | Monitor pipeline health in Cloud Logging | Cannot identify which function is causing slowdowns without latency metrics |
| Developer | Debug performance issues | No visibility into file size impact on processing time |
| Data Platform Lead | Track SLA compliance | Cannot measure end-to-end latency or correlate with file sizes |

---

## Goals

What success looks like (prioritized):

| Priority | Goal |
|----------|------|
| **MUST** | Add function-level latency timing (milliseconds) to all 4 pipeline functions |
| **MUST** | Log input file sizes (bytes) at function entry for all functions that read files |
| **MUST** | Log output file sizes (bytes) at function exit where files are produced |
| **SHOULD** | Use consistent field names across all functions (`latency_ms`, `input_size_bytes`, `output_size_bytes`) |
| **COULD** | Add a utility helper for timing measurements to reduce boilerplate |

**Priority Guide:**
- **MUST** = MVP fails without this
- **SHOULD** = Important, but workaround exists
- **COULD** = Nice-to-have, cut first if needed

---

## Success Criteria

Measurable outcomes (must include numbers):

- [ ] All 4 functions log `latency_ms` in completion messages (100% coverage)
- [ ] File read operations log `input_size_bytes` (bytes read from GCS)
- [ ] File write operations log `output_size_bytes` (bytes written to GCS)
- [ ] Field names are consistent across all functions (standardized naming)
- [ ] Metrics appear correctly in Cloud Logging JSON format (valid JSON structure)

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | tiff_to_png latency | A TIFF file is processed | Function completes | Logs include `latency_ms` > 0 in "Conversion complete" message |
| AT-002 | tiff_to_png sizes | A TIFF file is converted | Function completes | Logs include `input_size_bytes` and `output_size_bytes` |
| AT-003 | invoice_classifier latency | Converted invoice processed | Function completes | Logs include `latency_ms` > 0 in "Classification complete" message |
| AT-004 | invoice_classifier sizes | PNG files downloaded | Files downloaded | Logs include `total_input_bytes` (sum of all PNGs) |
| AT-005 | data_extractor timing | Invoice extracted | Function completes | Logs include function-level `latency_ms` separate from LLM latency |
| AT-006 | bigquery_writer latency | Data written to BigQuery | Function completes | Logs include `latency_ms` > 0 in completion message |
| AT-007 | Cloud Logging format | Any function executes | Logs streamed | All metrics appear as JSON fields, not in message text |

---

## Out of Scope

Explicitly NOT included in this feature:

- Adding new Cloud Monitoring metrics (logs-based only)
- Implementing OpenTelemetry tracing spans
- Adding memory usage or CPU metrics
- Modifying LangFuse observability (separate feature)
- Adding retry timing metrics (handled by DLQ)
- Dashboard creation in Cloud Logging

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Technical | Must use existing `StructuredLogFormatter` | No changes to logging infrastructure |
| Technical | Must use `extra={}` dict pattern for structured fields | Consistent with existing code style |
| Timeline | Part of April 1 production launch | Must complete before MVP |
| Resource | No additional cloud services | Logs-only approach |

---

## Technical Context

> Essential context for Design phase - prevents misplaced files and missed infrastructure needs.

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `functions/gcp/v1/src/functions/*/main.py` | 4 function entry points |
| **KB Domains** | gcp | Cloud Logging structured logs |
| **IaC Impact** | None | No infrastructure changes needed |

**Why This Matters:**

- **Location** → Design phase targets the 4 main.py files plus potentially a shared timing utility
- **KB Domains** → GCP KB contains Cloud Logging patterns
- **IaC Impact** → Pure code change, no Terraform updates

---

## Assumptions

Assumptions that if wrong could invalidate the design:

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | Cloud Logging automatically indexes JSON fields | Would need to add log-based metrics manually | [x] (standard GCP behavior) |
| A-002 | `time.perf_counter()` is available in Cloud Run runtime | Would need alternative timing method | [x] (Python standard library) |
| A-003 | Extra fields don't significantly increase log costs | Would need to evaluate log volume | [ ] |

**Note:** Validate critical assumptions before DESIGN phase. Unvalidated assumptions become risks.

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Clear gap: inconsistent/missing timing and size metrics |
| Users | 3 | Well-defined: DevOps, Developers, Platform Lead |
| Goals | 3 | Specific: latency_ms, input/output sizes, 4 functions |
| Success | 3 | Measurable: 100% coverage, valid JSON, consistent naming |
| Scope | 2 | Clear exclusions, but utility helper is borderline COULD |
| **Total** | **14/15** | |

**Scoring Guide:**
- 0 = Missing entirely
- 1 = Vague or incomplete
- 2 = Clear but missing details
- 3 = Crystal clear, actionable

**Minimum to proceed: 12/15**

---

## Open Questions

None - ready for Design.

---

## Implementation Notes

### Current State Analysis

| Function | Has Latency? | Has File Sizes? | Gaps |
|----------|--------------|-----------------|------|
| `tiff_to_png` | No | Partial (`size_bytes` on download) | Function latency, output sizes |
| `invoice_classifier` | No | No | Function latency, input sizes |
| `data_extractor` | Yes (LLM only) | No | Function latency, input sizes |
| `bigquery_writer` | No (upstream only) | N/A | Function latency |

### Proposed Field Names

```python
# Timing (milliseconds)
"latency_ms": 1234  # Total function execution time

# Input sizes
"input_size_bytes": 56789        # Single file
"total_input_bytes": 123456      # Multiple files

# Output sizes
"output_size_bytes": 34567       # Single file
"total_output_bytes": 456789     # Multiple files
```

### Timing Pattern

```python
import time

start_time = time.perf_counter()
# ... function logic ...
latency_ms = int((time.perf_counter() - start_time) * 1000)

logger.info("Function complete", extra={"latency_ms": latency_ms})
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-31 | define-agent | Initial version |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_PIPELINE_OBSERVABILITY_METRICS.md`
