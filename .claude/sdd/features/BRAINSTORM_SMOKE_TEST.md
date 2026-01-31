# BRAINSTORM: Smoke Test Framework

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | SMOKE_TEST |
| **Date** | 2026-01-30 |
| **Author** | brainstorm-agent |
| **Status** | Ready for Define |

---

## Initial Idea

**Raw Input:** Build an end-to-end Smoke Test framework for the invoice processing pipeline. The smoke test should validate the complete flow from invoice generation to BigQuery output, with observability at each stage.

**Context Gathered:**
- Existing synthetic invoice generator at `gen/synthetic_invoice_gen/` with CLI, Pydantic schemas, TIFF output
- Invoice extractor implementation at `src/invoice_extractor/` with models, validator, LLM gateway
- Pipeline architecture fully designed: 4 Cloud Run functions with GCS folder flow (landing → converted → classified → extracted → loaded)
- Sample TIFF invoices available for testing
- Target accuracy: ≥90% per requirements document

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|-------------|
| Likely Location | `tests/smoke/` | New test module alongside unit tests |
| Relevant KB Domains | gcp, pydantic, gemini | Storage, validation, extraction patterns |
| IaC Patterns | N/A for MVP | CI/CD integration deferred |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Primary trigger for running smoke tests? | On every deployment | Must integrate with deployment pipeline, exit code matters |
| 2 | What happens when a stage fails? | Fail fast + block deployment | Circuit breaker pattern, no retries needed |
| 3 | What test data strategy? | Generate synthetic + validate | Use invoice-gen CLI for fresh invoices with known ground truth |
| 4 | How should accuracy validation work? | Exact match on critical fields | invoice_id, total_amount must match; others can be fuzzy |
| 5 | Available sample data? | invoice-gen CLI + sample TIFFs | Strong foundation for test fixtures |

---

## Sample Data Inventory

> Samples improve test reliability through known ground truth.

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Invoice Generator | `gen/synthetic_invoice_gen/` | CLI | Produces TIFF + ground truth JSON |
| Sample TIFFs | User-provided | Multiple | Available for fixtures |
| Ground truth | Generated at runtime | N/A | invoice-gen produces matching JSON |
| Related code | `src/invoice_extractor/` | Full module | Models, validator, extractor ready |

**How samples will be used:**

- invoice-gen CLI generates TIFF with known field values
- Ground truth JSON stored alongside TIFF during generation
- Smoke test compares extracted values vs ground truth

---

## Approaches Explored

### Approach A: Monolithic CLI Smoke Runner ⭐ Recommended

**Description:** A single Python CLI (`smoke-test`) that orchestrates all 6 stages sequentially, calling GCP APIs directly and generating a unified JSON report.

**Pros:**
- Simple, single entry point
- Easy future CI/CD integration (exit code 0/1)
- Fast iteration during development
- Shares code with invoice-gen

**Cons:**
- Polls GCS/BigQuery (not truly event-driven)
- Less realistic than testing via actual Pub/Sub flow

**Why Recommended:** Matches "fail fast" requirement, provides quick feedback, minimal infrastructure overhead for MVP.

---

### Approach B: Pytest Stage Functions

**Description:** Each stage is a pytest test class with fixtures for state passing.

**Pros:**
- Familiar pytest ecosystem
- Built-in assertion framework

**Cons:**
- Fixtures for cross-test state are awkward
- No built-in timeout/retry per stage

---

### Approach C: Cloud-Native Event-Driven Test

**Description:** Deploy a test harness Cloud Run function that sends test invoices through actual Pub/Sub topics.

**Pros:**
- Tests the real event flow
- Catches Pub/Sub configuration issues

**Cons:**
- Much more complex to implement
- Harder to debug failures
- Requires test-specific infrastructure

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach A (CLI Runner) |
| **User Confirmation** | 2026-01-30 |
| **Reasoning** | Fast feedback, simple implementation, matches "fail fast" requirement, future CI/CD ready |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|----------------------|
| 1 | CLI-based runner (not pytest) | Single entry point, easier CI/CD integration | pytest stage functions (awkward fixtures) |
| 2 | Synthetic invoice generation | Known ground truth, realistic testing | Golden fixtures only (less realistic) |
| 3 | Exact match on critical fields | Clear pass/fail, matches 90% accuracy target | Fuzzy matching everywhere (too lenient) |
| 4 | Fail fast on any stage failure | Tight feedback loop, no wasted time | Continue + report all (delays feedback) |
| 5 | JSON output format | Machine-parseable, CI/CD compatible | HTML reports (nice but not essential) |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|-------------------|----------------|----------------|
| HTML report generation | JSON is sufficient for CI/CD | Yes |
| Scheduled runs | Primary trigger is on-deployment | Yes |
| Staging environment | Project only has dev/prod | No (N/A) |
| LangFuse trace validation | Adds complexity, not critical for MVP | Yes |
| Retry with backoff | Contradicts "fail fast" choice | Yes |
| Multi-vendor parallel testing | Test one vendor at a time for MVP | Yes |
| CI/CD integration | Focus on CLI first | Yes |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---------|-----------|---------------|-----------|
| CLI structure and folder layout | ✅ | Approved | No |
| 6-stage flow diagram | ✅ | Approved | No |
| CI/CD integration | ✅ | Deferred to post-MVP | Yes - removed from scope |
| Configuration file structure | ✅ | Approved | No |

---

## Suggested Requirements for /define

Based on this brainstorm session, the following should be captured in the DEFINE phase:

### Problem Statement (Draft)

The invoice processing pipeline lacks automated end-to-end validation to catch regressions before production deployment.

### Target Users (Draft)

| User | Pain Point |
|------|------------|
| Developer | No quick way to validate changes work end-to-end |
| DevOps | No gate to prevent broken deployments |
| Data Team | No confidence that extraction accuracy is maintained |

### Success Criteria (Draft)

- [ ] CLI can run full 6-stage smoke test in under 2 minutes
- [ ] Exit code 0 for all stages passing, 1 for any failure
- [ ] JSON output includes stage-by-stage timing and pass/fail
- [ ] Critical field validation catches accuracy regressions
- [ ] Works with dev and prod environments

### Constraints Identified

- Must use existing invoice-gen CLI for test data
- Must poll GCS (Cloud Run is event-driven but test runner is not)
- 60-second timeout for pipeline processing stage

### Out of Scope (Confirmed)

- HTML report generation
- Scheduled/periodic runs
- LangFuse trace validation
- Automatic retry on failure
- Multi-vendor parallel testing
- CI/CD workflow files (deferred)

---

## Session Summary

| Metric | Value |
|--------|-------|
| Questions Asked | 5 |
| Approaches Explored | 3 |
| Features Removed (YAGNI) | 7 |
| Validations Completed | 4 |
| Duration | ~15 minutes |

---

## Proposed CLI Interface

```bash
# Full smoke test
smoke-test run --env dev --vendor ubereats

# With fresh synthetic invoice
smoke-test run --env dev --generate

# With existing TIFF
smoke-test run --env dev --invoice tests/fixtures/ubereats_001.tiff

# Skip specific stage
smoke-test run --env dev --skip-stage bigquery

# Output JSON report to file
smoke-test run --env dev --output results.json
```

---

## Proposed Folder Structure

```
tests/
└── smoke/
    ├── __init__.py
    ├── cli.py                    # Click CLI entry point
    ├── runner.py                 # Stage orchestrator
    ├── stages/
    │   ├── __init__.py
    │   ├── generate.py           # Stage 1: Generate invoice
    │   ├── upload.py             # Stage 2: Upload to GCS
    │   ├── process.py            # Stage 3: Wait for pipeline
    │   ├── validate.py           # Stage 4: Compare extraction
    │   ├── bigquery.py           # Stage 5: Verify BQ row
    │   └── logging.py            # Stage 6: Check Cloud Logs
    ├── validators/
    │   ├── __init__.py
    │   ├── field_matcher.py      # Exact match for critical fields
    │   └── schema_checker.py     # Pydantic validation
    ├── config/
    │   └── smoke_config.yaml     # Timeouts, thresholds, env config
    └── fixtures/                 # Optional pre-generated invoices
        └── ubereats_golden.tiff
```

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_SMOKE_TEST.md`

---

## Stage Flow Reference

```
STAGE 1: GENERATE
├── Use invoice-gen CLI to create TIFF + ground truth JSON
│
STAGE 2: UPLOAD
├── Upload TIFF to GCS landing/ folder
│
STAGE 3: PROCESS (Poll)
├── Poll GCS folders until extracted/ has result
├── Timeout: 60 seconds
│
STAGE 4: VALIDATE EXTRACTION
├── Download extracted JSON
├── Compare critical fields (exact match)
├── Compare other fields (fuzzy tolerance)
│
STAGE 5: VERIFY BIGQUERY
├── Query BQ table for invoice_id
├── Verify row exists with expected values
│
STAGE 6: CHECK LOGS
├── Query Cloud Logging for errors
├── Verify no ERROR level for invoice_id
│
EXIT
├── Code 0: All stages passed
├── Code 1: Any stage failed (report which)
```
