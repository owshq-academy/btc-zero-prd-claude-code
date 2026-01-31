# DEFINE: Smoke Test Framework

> End-to-end validation CLI for the invoice processing pipeline that tests the complete flow from invoice generation to BigQuery output

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | SMOKE_TEST |
| **Date** | 2026-01-30 |
| **Author** | define-agent |
| **Status** | Ready for Design |
| **Clarity Score** | 15/15 |
| **Source** | [BRAINSTORM_SMOKE_TEST.md](BRAINSTORM_SMOKE_TEST.md) |

---

## Problem Statement

The invoice processing pipeline currently lacks automated end-to-end validation to catch regressions before production deployment. Developers have no quick way to verify changes work across all 4 Cloud Run functions, DevOps has no gate to prevent broken deployments, and the Data Team has no confidence that extraction accuracy is maintained after code changes.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| **Developer** | Builds and modifies pipeline functions | No quick way to validate changes work end-to-end; must manually test each stage |
| **DevOps** | Manages deployment pipeline | No automated gate to prevent broken deployments; relies on post-deployment monitoring |
| **Data Team** | Consumes extracted data | No confidence that extraction accuracy is maintained; discovers regressions after data lands in BigQuery |

---

## Goals

What success looks like (prioritized):

| Priority | Goal |
|----------|------|
| **MUST** | Run all 6 stages (generate, upload, process, validate, bigquery, logs) sequentially with pass/fail per stage |
| **MUST** | Exit with code 0 on success, code 1 on failure (for CI/CD integration) |
| **MUST** | Compare extracted data against ground truth with exact match on critical fields |
| **MUST** | Support dev and prod environment targeting |
| **SHOULD** | Output JSON report with stage-by-stage timing and results |
| **SHOULD** | Use existing invoice-gen CLI to generate test invoices with known ground truth |
| **COULD** | Allow skipping individual stages for debugging |
| **COULD** | Accept existing TIFF as input instead of generating new one |

---

## Success Criteria

Measurable outcomes:

- [ ] **SC-001:** CLI can run full 6-stage smoke test in under 2 minutes
- [ ] **SC-002:** Exit code 0 when all stages pass, exit code 1 when any stage fails
- [ ] **SC-003:** JSON output includes stage name, pass/fail, duration (ms), and error message (if failed)
- [ ] **SC-004:** Critical field validation catches extraction regressions (invoice_id, total_amount, vendor_type must match exactly)
- [ ] **SC-005:** Works with both dev (`eda-gemini-dev`) and prod (`eda-gemini-prd`) environments
- [ ] **SC-006:** Fails fast on first stage failure (no wasted time on subsequent stages)

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Happy path - full smoke test passes | Pipeline is healthy, dev environment is accessible | `smoke-test run --env dev --vendor ubereats` | All 6 stages pass, exit code 0, JSON shows all stages "passed" |
| AT-002 | Fail fast on upload failure | GCS bucket is inaccessible (wrong credentials) | `smoke-test run --env dev` | Stage 2 (upload) fails, stages 3-6 are skipped, exit code 1 |
| AT-003 | Extraction accuracy regression | Pipeline extracts total_amount as 45.76 instead of 45.67 | `smoke-test run --env dev` | Stage 4 (validate) fails with "total_amount mismatch: expected 45.67, got 45.76" |
| AT-004 | BigQuery row missing | Extraction succeeds but BigQuery write fails | `smoke-test run --env dev` | Stage 5 (bigquery) fails with "row not found for invoice_id" |
| AT-005 | Skip stage for debugging | Developer wants to skip BigQuery verification | `smoke-test run --env dev --skip-stage bigquery` | Stages 1-4 and 6 run, stage 5 skipped, exit code based on remaining stages |
| AT-006 | Custom invoice input | Developer has existing TIFF to test | `smoke-test run --env dev --invoice tests/fixtures/ubereats_001.tiff` | Stage 1 (generate) is skipped, uses provided TIFF |
| AT-007 | Timeout during processing | Pipeline takes longer than 60 seconds | `smoke-test run --env dev` | Stage 3 (process) fails with "timeout: waited 60s for extracted/ result" |
| AT-008 | JSON output to file | DevOps needs artifacts for CI/CD | `smoke-test run --env dev --output results.json` | results.json contains full report; stdout shows summary |

---

## Out of Scope

Explicitly NOT included in this feature (MVP):

- **HTML report generation** - JSON output is sufficient for CI/CD; can add HTML later
- **Scheduled/periodic runs** - Primary trigger is on-deployment; scheduling is a future enhancement
- **LangFuse trace validation** - Nice-to-have but adds complexity; defer to v2
- **Automatic retry on failure** - "Fail fast" chosen over retry; contradicts design decision
- **Multi-vendor parallel testing** - Test one vendor at a time for MVP (UberEats first)
- **CI/CD workflow files** - Focus on CLI first; integration comes after CLI works
- **Staging environment** - Project only has dev/prod; staging doesn't exist

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| **Technical** | Must use existing `invoice-gen` CLI for test data generation | Cannot create a new generator; reuse existing code |
| **Technical** | Must poll GCS for pipeline progress (Cloud Run is event-driven) | Add polling logic with configurable interval (2s) and timeout (60s) |
| **Technical** | Critical fields must match exactly: `invoice_id`, `total_amount`, `vendor_type`, `currency` | Field matcher must distinguish exact vs fuzzy match requirements |
| **Timeline** | Must work before April 1, 2026 production launch | Keep scope minimal; no over-engineering |
| **Resource** | No new GCP infrastructure for testing | Use existing buckets, topics, tables with test prefixes |

---

## Technical Context

> Essential context for Design phase - prevents misplaced files and missed infrastructure needs.

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `tests/smoke/` | New test module alongside existing tests |
| **KB Domains** | gcp, pydantic | GCS/BigQuery access patterns, Pydantic validation |
| **IaC Impact** | None | Uses existing infrastructure; no new resources |
| **Related Code** | `gen/synthetic_invoice_gen/`, `src/invoice_extractor/` | Reuse invoice-gen, reference extractor models |

**Why This Matters:**

- **Location** → `tests/smoke/` keeps test code separate from production code
- **KB Domains** → GCP patterns for storage/BigQuery access, Pydantic for validation
- **IaC Impact** → No Terraform changes needed; uses existing dev/prod infrastructure

---

## Assumptions

Assumptions that if wrong could invalidate the design:

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | Pipeline processing completes in < 60 seconds (P95 target) | Would need longer timeout, may affect CI/CD pipeline duration | [x] Per requirements doc |
| A-002 | invoice-gen CLI produces valid ground truth JSON alongside TIFF | Would need to extract expected values differently | [x] Verified in brainstorm |
| A-003 | GCS polling at 2-second intervals is sufficient to detect completion | May miss completion or poll unnecessarily; tune if needed | [ ] |
| A-004 | BigQuery row is queryable immediately after write | May need to wait for streaming buffer; add short delay if needed | [ ] |
| A-005 | Cloud Logging entries are available within 5 minutes of generation | May need longer lookback window for log validation | [ ] |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Clear: pipeline lacks E2E validation, causing deployment risk |
| Users | 3 | Three users with specific pain points |
| Goals | 3 | Prioritized with MUST/SHOULD/COULD |
| Success | 3 | Measurable: "under 2 minutes", "exit code 0/1" |
| Scope | 3 | 7 explicit exclusions, 5 constraints |
| **Total** | **15/15** | |

---

## CLI Interface (Reference)

```bash
# Full smoke test with synthetic invoice
smoke-test run --env dev --vendor ubereats

# Generate fresh invoice (explicit)
smoke-test run --env dev --generate

# Use existing TIFF
smoke-test run --env dev --invoice tests/fixtures/ubereats_001.tiff

# Skip specific stage
smoke-test run --env dev --skip-stage bigquery

# Output JSON report to file
smoke-test run --env dev --output results.json

# Verbose output for debugging
smoke-test run --env dev --verbose
```

---

## Stage Definitions (Reference)

| Stage | Name | Input | Output | Timeout | Pass Condition |
|-------|------|-------|--------|---------|----------------|
| 1 | `generate` | vendor type | TIFF + ground truth JSON | 30s | Files created successfully |
| 2 | `upload` | TIFF file path | GCS object path | 10s | Object exists in landing/ |
| 3 | `process` | GCS object path | Extracted JSON path | 60s | JSON appears in extracted/ |
| 4 | `validate` | Extracted JSON + ground truth | Comparison result | 10s | Critical fields match exactly |
| 5 | `bigquery` | invoice_id | BQ row | 15s | Row exists with expected values |
| 6 | `logging` | invoice_id | Log entries | 10s | No ERROR level entries for invoice |

---

## Critical Fields (Exact Match Required)

| Field | Type | Example | Match Rule |
|-------|------|---------|------------|
| `invoice_id` | String | "INV-UE-308774" | Exact match |
| `vendor_type` | Enum | "ubereats" | Exact match |
| `total_amount` | Float | 45.67 | Exact match (no tolerance) |
| `currency` | String | "USD" | Exact match |

**Other fields:** Validated but can have fuzzy tolerance or be optional for MVP.

---

## Open Questions

None - ready for Design.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-30 | define-agent | Initial version from BRAINSTORM_SMOKE_TEST.md |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_SMOKE_TEST.md`
