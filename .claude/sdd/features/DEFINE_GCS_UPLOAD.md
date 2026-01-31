# DEFINE: GCS Upload for Synthetic Invoice Generator

> Add optional GCS upload capability to enable end-to-end pipeline testing

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | GCS_UPLOAD |
| **Date** | 2026-01-30 |
| **Author** | define-agent |
| **Status** | Ready for Design |
| **Clarity Score** | 15/15 |
| **Source** | BRAINSTORM_GCS_UPLOAD.md |

---

## Problem Statement

The synthetic invoice generator (`invoice-gen`) outputs TIFF files to the local filesystem only, requiring developers to manually upload files to GCS to test the full extraction pipeline (TIFF→PNG→Extract→BigQuery). This manual step slows down end-to-end testing and creates friction when validating extraction accuracy.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Developer | Implements and tests extraction features | Must manually upload test invoices via `gsutil` or console to trigger pipeline |
| QA Engineer | Validates extraction accuracy | Cannot easily run automated end-to-end tests with fresh synthetic data |

---

## Goals

| Priority | Goal |
|----------|------|
| **MUST** | Upload generated TIFF files to a specified GCS bucket via CLI flag |
| **MUST** | Preserve existing local-only behavior when GCS flag not provided |
| **MUST** | Report upload success/failure counts in CLI output |
| **SHOULD** | Handle upload failures gracefully without stopping remaining uploads |
| **COULD** | Support dry-run mode to preview what would be uploaded |

---

## Success Criteria

Measurable outcomes:

- [ ] `--gcs-bucket` flag accepts a bucket name and uploads all generated files
- [ ] Files uploaded to GCS root with same naming convention: `{vendor}_{invoice_id}_{date}.tiff`
- [ ] Upload failures logged with warning but don't stop batch (warn-and-continue)
- [ ] CLI output shows: `Uploaded: X/Y files (Z failed)`
- [ ] Existing behavior unchanged when `--gcs-bucket` not provided
- [ ] Authentication uses ADC (Application Default Credentials) only

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Happy path upload | Generator configured with `--gcs-bucket bucket-dev` | Generate 5 invoices | All 5 files appear in `gs://bucket-dev/` with correct names |
| AT-002 | Local-only (backward compat) | Generator configured without `--gcs-bucket` | Generate 5 invoices | Files created locally, no GCS interaction |
| AT-003 | Partial upload failure | GCS bucket exists but 1 file fails (e.g., quota) | Generate 5 invoices | 4 files uploaded, 1 failure logged, CLI shows "4/5 uploaded (1 failed)" |
| AT-004 | Invalid bucket | `--gcs-bucket nonexistent-bucket` | Generate 1 invoice | Clear error message about bucket access, local file still exists |
| AT-005 | No ADC credentials | No `gcloud auth` and no `GOOGLE_APPLICATION_CREDENTIALS` | Use `--gcs-bucket` | Clear error message about authentication before generation starts |
| AT-006 | Combined with other flags | `--gcs-bucket bucket-dev --all-partners --count 2` | Generate | 10 files generated locally and uploaded to GCS |

---

## Out of Scope

Explicitly NOT included in this feature:

- **Streaming upload** — Files always written locally first (simplicity over I/O optimization)
- **Service account key file authentication** — ADC only, no `--credentials` flag
- **Environment variable configuration** — No `GCS_BUCKET` env var fallback
- **Path prefix/subfolder organization** — Flat upload to bucket root only
- **Parallel uploads** — Sequential upload sufficient for 1-10 files
- **Exponential backoff retry** — Simple single retry on failure
- **Separate `upload` subcommand** — Integrated into existing `invoice-gen` command
- **Dry-run mode** — Deferred to future (marked as COULD)

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Technical | ADC-only authentication | No credential file handling code needed |
| Technical | Sequential uploads | Simple implementation, no async/threading |
| Technical | Flat path structure | No path manipulation logic |
| Volume | Small batches (1-10 files) | No optimization for large batches |
| Dependency | New: `google-cloud-storage>=2.10.0` | Add to pyproject.toml |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `gen/synthetic_invoice_gen/src/invoice_gen/` | Add `gcs/` submodule |
| **KB Domains** | gcp (concepts/gcs.md) | Use `upload_from_filename` pattern |
| **IaC Impact** | None | Buckets already exist (`invoices-input-dev/prod`) |

**New Module Structure:**
```text
src/invoice_gen/
├── gcs/
│   ├── __init__.py
│   └── uploader.py   # GCSUploader class
└── cli.py            # Add --gcs-bucket flag
```

**New Dependency:**
```toml
# pyproject.toml [project.dependencies]
google-cloud-storage>=2.10.0
```

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | User has `gcloud auth application-default login` configured | Upload fails with auth error — this is expected behavior | [x] Documented |
| A-002 | Target bucket already exists and user has write access | Upload fails with clear error — this is expected behavior | [x] Documented |
| A-003 | Small batch size (1-10 files) remains typical use case | Would need parallel uploads for performance | [ ] Monitor usage |
| A-004 | GCS client library handles retries internally | May need explicit retry wrapper | [ ] Test |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Specific pain point with clear impact |
| Users | 3 | Two personas with distinct pain points |
| Goals | 3 | Prioritized with MUST/SHOULD/COULD |
| Success | 3 | Measurable criteria with numbers |
| Scope | 3 | 7 explicit exclusions from YAGNI |
| **Total** | **15/15** | |

---

## Open Questions

None — ready for Design.

All questions were resolved during the BRAINSTORM phase:
- Use case: End-to-end testing ✓
- Volume: Small batches ✓
- Auth: ADC only ✓
- Bucket config: CLI flag only ✓
- Path structure: Flat ✓
- Error handling: Warn and continue ✓

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-30 | define-agent | Initial version from BRAINSTORM_GCS_UPLOAD.md |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_GCS_UPLOAD.md`
