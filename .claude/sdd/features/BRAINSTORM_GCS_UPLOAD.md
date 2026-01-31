# BRAINSTORM: GCS Upload for Synthetic Invoice Generator

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | GCS_UPLOAD |
| **Date** | 2026-01-30 |
| **Author** | brainstorm-agent |
| **Status** | Ready for Define |

---

## Initial Idea

**Raw Input:** Add GCS upload capability to the synthetic invoice generator (gen/synthetic_invoice_gen). The generator currently outputs TIFF/PNG/HTML files locally. User wants to optionally send generated invoices directly to a GCS bucket to enable end-to-end pipeline testing.

**Context Gathered:**
- Existing CLI uses Click with well-structured options
- Generator has clean separation: data generation → HTML → PDF → TIFF
- GCP KB shows established bucket naming: `invoices-input`, `invoices-processed`
- No cloud dependencies currently in pyproject.toml
- Existing file naming: `{vendor}_{invoice_id}_{date}.tiff`

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|-------------|
| Likely Location | `gen/synthetic_invoice_gen/src/invoice_gen/` | Add GCS uploader module |
| Relevant KB Domains | gcp (concepts/gcs.md) | Use established patterns |
| IaC Patterns | N/A | No infrastructure changes needed |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | What is the primary use case for GCS upload? | End-to-end testing | Files go to input bucket to trigger pipeline |
| 2 | What volume and frequency do you expect? | Small batches (1-10) | No parallel uploads needed |
| 3 | How will you authenticate to GCS? | ADC (local gcloud) | No credential file handling |
| 4 | How do you want to specify the target bucket? | CLI flag only | No env var fallback |
| 5 | Should files be organized in subfolders? | Flat (root level) | No path prefix logic |
| 6 | How should upload failures be handled? | Warn and continue | Resilient, report summary at end |

---

## Sample Data Inventory

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Input files | `gen/synthetic_invoice_gen/samples/` | 10 | Sample TIFFs by vendor |
| Output examples | `examples/` | 10 | Additional sample outputs |
| Ground truth | N/A | - | Not applicable |
| Related code | `gen/synthetic_invoice_gen/src/invoice_gen/cli.py` | 1 | CLI patterns to follow |

**How samples will be used:**
- File naming convention: `{vendor}_{invoice_id}_{date}.tiff`
- Existing CLI patterns for new flag implementation

---

## Approaches Explored

### Approach A: CLI Flag Extension ⭐ Recommended

**Description:** Add a `--gcs-bucket` flag to the existing CLI. When provided, upload files to GCS after local generation.

**Example Usage:**
```bash
# Local only (current behavior)
invoice-gen --partner ubereats --count 5 --output ./output

# Upload to GCS
invoice-gen --partner ubereats --count 5 --gcs-bucket invoices-input-dev
```

**Pros:**
- Minimal changes to existing code
- Local output still works (no breaking changes)
- GCS upload is additive, not required
- Clean separation: generate locally → upload to GCS

**Cons:**
- Still writes to local disk first (disk I/O)
- Two-step process internally

**Why Recommended:** Simplest implementation, preserves backward compatibility, matches small batch requirements.

---

### Approach B: Streaming Upload (Skip Local)

**Description:** Stream directly to GCS without writing to local disk.

**Pros:**
- No local disk I/O
- Cleaner for CI/CD pipelines

**Cons:**
- More complex implementation
- Loses local backup if GCS fails
- Over-engineered for 1-10 files

---

### Approach C: Separate Upload Command

**Description:** Create a new `invoice-gen upload` subcommand.

**Pros:**
- Complete separation of concerns

**Cons:**
- Two commands instead of one
- More CLI complexity

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach A (CLI Flag Extension) |
| **User Confirmation** | 2026-01-30 |
| **Reasoning** | Simplest implementation, preserves backward compatibility |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|----------------------|
| 1 | ADC-only authentication | Simplicity, user already uses gcloud | Service account key file support |
| 2 | CLI flag only (no env var) | Explicit configuration | Environment variable fallback |
| 3 | Flat upload (no subfolders) | Matches current naming convention | Vendor subfolders |
| 4 | Warn and continue on errors | Resilient batch behavior | Fail fast |
| 5 | Local files always kept | Debugging capability | Optional local cleanup |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|-------------------|----------------|----------------|
| Streaming upload | Over-engineered for 1-10 files | Yes |
| Parallel uploads | Not needed for small batches | Yes |
| Service account key support | ADC is sufficient for local dev | Yes |
| Environment variable config | CLI flag is explicit enough | Yes |
| Path prefix/subfolders | Flat upload matches current pattern | Yes |
| Exponential backoff retry | Simple retry is enough | Yes |
| Separate upload command | One command is cleaner | Yes |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---------|-----------|---------------|-----------|
| Approach selection | ✅ | Confirmed Approach A | No |
| Error handling strategy | ✅ | Confirmed warn-and-continue | No |

---

## Suggested Requirements for /define

Based on this brainstorm session, the following should be captured in the DEFINE phase:

### Problem Statement (Draft)
The synthetic invoice generator outputs files locally, requiring manual GCS upload to test the full extraction pipeline end-to-end.

### Target Users (Draft)
| User | Pain Point |
|------|------------|
| Developer | Must manually upload test invoices to GCS to trigger pipeline |
| QA Engineer | Cannot easily run automated end-to-end tests |

### Success Criteria (Draft)
- [ ] `--gcs-bucket` flag uploads generated files to specified bucket
- [ ] Files uploaded with same naming convention as local output
- [ ] Upload failures logged but don't stop remaining uploads
- [ ] Summary shows successful/failed upload counts
- [ ] Existing local-only behavior unchanged when flag not provided

### Constraints Identified
- ADC authentication only (no service account key files)
- Small batch sizes (1-10 files) — no parallel optimization needed
- Flat path structure (no subfolders)

### Out of Scope (Confirmed)
- Streaming upload (skip local)
- Service account key file authentication
- Environment variable configuration
- Path prefix/subfolder organization
- Complex retry strategies
- Separate upload command

---

## Implementation Notes

### New Dependency
```toml
# pyproject.toml
google-cloud-storage>=2.10.0
```

### New Module Structure
```text
src/invoice_gen/
├── gcs/
│   ├── __init__.py
│   └── uploader.py   # GCSUploader class
└── cli.py            # Add --gcs-bucket flag
```

### CLI Changes
```python
@click.option(
    "--gcs-bucket",
    type=str,
    default=None,
    help="GCS bucket to upload generated files (requires gcloud auth)",
)
```

---

## Session Summary

| Metric | Value |
|--------|-------|
| Questions Asked | 6 |
| Approaches Explored | 3 |
| Features Removed (YAGNI) | 7 |
| Validations Completed | 2 |

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_GCS_UPLOAD.md`
