# DESIGN: GCS Upload for Synthetic Invoice Generator

> Technical design for implementing GCS upload capability in the invoice generator CLI

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | GCS_UPLOAD |
| **Date** | 2026-01-30 |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_GCS_UPLOAD.md](./DEFINE_GCS_UPLOAD.md) |
| **Status** | Ready for Build |

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        invoice-gen CLI                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                       cli.py (Modified)                       │   │
│  │  @click.option("--gcs-bucket", ...)                          │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                         │                                            │
│                         ▼                                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    InvoiceGenerator                           │   │
│  │  generate_tiff() → Path (local file)                         │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                         │                                            │
│                         ▼                                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    gcs/uploader.py (New)                      │   │
│  │  GCSUploader.upload_file(local_path) → UploadResult          │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                         │                                            │
│                         ▼                                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Google Cloud Storage                       │   │
│  │  gs://{bucket}/{filename}.tiff                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| `cli.py` | CLI entry point with new `--gcs-bucket` flag | Click 8.1+ |
| `gcs/__init__.py` | Package exports | Python |
| `gcs/uploader.py` | GCS upload logic with error handling | google-cloud-storage |
| `test_gcs_uploader.py` | Unit tests for uploader | pytest + mocks |
| `test_cli.py` | Extended CLI tests for GCS flag | pytest + CliRunner |

---

## Key Decisions

### Decision 1: Separate GCSUploader Class

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** The upload logic needs to live somewhere. Options were: (1) inline in CLI, (2) add to InvoiceGenerator, (3) separate module.

**Choice:** Create a dedicated `gcs/uploader.py` module with a `GCSUploader` class.

**Rationale:**
- Single Responsibility: CLI handles flags, Generator handles generation, Uploader handles cloud
- Testable: Can mock GCSUploader independently
- Extensible: Easy to add Azure/S3 uploaders later if needed

**Alternatives Rejected:**
1. Inline in CLI - Would make CLI harder to test and maintain
2. Add to InvoiceGenerator - Violates single responsibility, couples generation to cloud

**Consequences:**
- Slightly more files (acceptable for clean architecture)
- Clear separation of concerns
- Easy to unit test each component independently

---

### Decision 2: Upload After Generation (Not Streaming)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** Could upload files as they're generated (streaming) or after all files exist locally.

**Choice:** Upload sequentially after each file is generated locally. Local files always kept.

**Rationale:**
- Simpler implementation (no byte streaming)
- Local files available for debugging if GCS fails
- Small batch sizes (1-10) make streaming overhead unnecessary

**Alternatives Rejected:**
1. Streaming upload - Over-engineered for small batches
2. Batch upload at end - Delays feedback, user wants to see progress

**Consequences:**
- Double disk I/O (write local, read for upload) - acceptable for small files
- Local files always available as backup

---

### Decision 3: Warn and Continue Error Handling

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** Need to handle upload failures for individual files in a batch.

**Choice:** Log warning, continue with remaining files, report summary at end.

**Rationale:**
- Resilient: One failure doesn't waste entire batch
- Transparent: User sees exactly what succeeded/failed
- Consistent: Matches existing error handling pattern in CLI

**Alternatives Rejected:**
1. Fail fast - One failure loses entire batch
2. Silent skip - User wouldn't know about failures

**Consequences:**
- Must track success/failure counts
- Exit code should reflect partial failures (non-zero if any failures)

---

### Decision 4: Authentication Validation at Start

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** ADC might not be configured. When should we detect this?

**Choice:** Validate GCS access at CLI start (before generation) when `--gcs-bucket` is provided.

**Rationale:**
- Fail fast: Don't waste time generating files if upload will fail
- Clear error: User knows immediately if auth is missing
- Bucket validation: Also verifies bucket exists and is accessible

**Alternatives Rejected:**
1. Validate on first upload - Wastes generation time
2. Don't validate - Poor user experience

**Consequences:**
- Extra GCS API call at start (acceptable latency for UX benefit)
- Clear error message before generation begins

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `gen/synthetic_invoice_gen/src/invoice_gen/gcs/__init__.py` | Create | Package exports | @python-developer | None |
| 2 | `gen/synthetic_invoice_gen/src/invoice_gen/gcs/uploader.py` | Create | GCSUploader class | @python-developer | None |
| 3 | `gen/synthetic_invoice_gen/src/invoice_gen/cli.py` | Modify | Add --gcs-bucket flag | @python-developer | 2 |
| 4 | `gen/synthetic_invoice_gen/pyproject.toml` | Modify | Add google-cloud-storage dep | @python-developer | None |
| 5 | `gen/synthetic_invoice_gen/tests/test_gcs_uploader.py` | Create | Unit tests for uploader | @test-generator | 2 |
| 6 | `gen/synthetic_invoice_gen/tests/test_cli.py` | Modify | Add GCS flag tests | @test-generator | 3 |

**Total Files:** 6 (2 new, 4 modified)

---

## Agent Assignment Rationale

| Agent | Files Assigned | Why This Agent |
|-------|----------------|----------------|
| @python-developer | 1, 2, 3, 4 | Python code with type hints, Click patterns, GCP SDK |
| @test-generator | 5, 6 | pytest fixtures, mocks, CLI testing patterns |

**Agent Discovery:**
- Scanned: `.claude/agents/**/*.md`
- Matched by: Python file type, Click CLI, pytest testing

---

## Code Patterns

### Pattern 1: GCSUploader Class

```python
# gcs/uploader.py
"""GCS upload functionality for generated invoices."""

from dataclasses import dataclass
from pathlib import Path

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError


@dataclass
class UploadResult:
    """Result of a single file upload attempt."""

    local_path: Path
    gcs_uri: str | None
    success: bool
    error: str | None = None


class GCSUploader:
    """Handles uploading files to Google Cloud Storage."""

    def __init__(self, bucket_name: str):
        """Initialize uploader with target bucket.

        Args:
            bucket_name: GCS bucket name (without gs:// prefix)

        Raises:
            ValueError: If bucket is empty
            GoogleCloudError: If bucket doesn't exist or not accessible
        """
        if not bucket_name:
            raise ValueError("Bucket name cannot be empty")

        self.bucket_name = bucket_name
        self._client = storage.Client()
        self._bucket = self._client.bucket(bucket_name)

        # Validate bucket exists and is accessible
        if not self._bucket.exists():
            raise GoogleCloudError(f"Bucket '{bucket_name}' does not exist or is not accessible")

    def upload_file(self, local_path: Path) -> UploadResult:
        """Upload a single file to GCS.

        Args:
            local_path: Path to local file

        Returns:
            UploadResult with success/failure details
        """
        blob_name = local_path.name
        gcs_uri = f"gs://{self.bucket_name}/{blob_name}"

        try:
            blob = self._bucket.blob(blob_name)
            blob.upload_from_filename(
                str(local_path),
                content_type="image/tiff",
                timeout=300,
            )
            return UploadResult(
                local_path=local_path,
                gcs_uri=gcs_uri,
                success=True,
            )
        except GoogleCloudError as e:
            return UploadResult(
                local_path=local_path,
                gcs_uri=None,
                success=False,
                error=str(e),
            )
```

### Pattern 2: CLI Integration

```python
# cli.py additions

@click.option(
    "--gcs-bucket",
    type=str,
    default=None,
    help="GCS bucket to upload generated files (requires gcloud auth)",
)
def main(
    # ... existing params ...
    gcs_bucket: str | None,
) -> None:
    # Validate GCS access early (before generation)
    uploader: GCSUploader | None = None
    if gcs_bucket:
        try:
            from invoice_gen.gcs import GCSUploader
            uploader = GCSUploader(gcs_bucket)
            click.echo(f"  GCS bucket: gs://{gcs_bucket}/")
        except Exception as e:
            raise click.ClickException(f"GCS access failed: {e}")

    # ... generation loop ...

    # Upload after generation
    if uploader and generated_files:
        upload_success = 0
        upload_failed = 0

        click.echo()
        with click.progressbar(
            generated_files,
            label="Uploading to GCS",
            show_pos=True,
        ) as bar:
            for file_path in bar:
                result = uploader.upload_file(file_path)
                if result.success:
                    upload_success += 1
                else:
                    upload_failed += 1
                    click.echo(click.style(f"\n  ⚠ Upload failed: {file_path.name}: {result.error}", fg="yellow"))

        click.echo()
        if upload_failed == 0:
            click.echo(click.style(f"☁️  Uploaded: {upload_success}/{len(generated_files)} files to gs://{gcs_bucket}/", fg="green"))
        else:
            click.echo(click.style(f"☁️  Uploaded: {upload_success}/{len(generated_files)} files ({upload_failed} failed)", fg="yellow"))
```

### Pattern 3: Test with Mocks

```python
# test_gcs_uploader.py
"""Tests for GCS uploader."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from invoice_gen.gcs.uploader import GCSUploader, UploadResult


class TestGCSUploader:
    @patch("invoice_gen.gcs.uploader.storage.Client")
    def test_init_validates_bucket_exists(self, mock_client_class: MagicMock) -> None:
        """Uploader should validate bucket exists on init."""
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.exists.return_value = True
        mock_client.bucket.return_value = mock_bucket
        mock_client_class.return_value = mock_client

        uploader = GCSUploader("test-bucket")

        mock_client.bucket.assert_called_once_with("test-bucket")
        mock_bucket.exists.assert_called_once()
        assert uploader.bucket_name == "test-bucket"

    @patch("invoice_gen.gcs.uploader.storage.Client")
    def test_upload_file_success(self, mock_client_class: MagicMock, tmp_path: Path) -> None:
        """Successful upload should return UploadResult with success=True."""
        # Setup mocks
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob
        mock_client.bucket.return_value = mock_bucket
        mock_client_class.return_value = mock_client

        # Create test file
        test_file = tmp_path / "test.tiff"
        test_file.write_bytes(b"fake tiff content")

        uploader = GCSUploader("test-bucket")
        result = uploader.upload_file(test_file)

        assert result.success is True
        assert result.gcs_uri == "gs://test-bucket/test.tiff"
        assert result.error is None
        mock_blob.upload_from_filename.assert_called_once()
```

---

## Data Flow

```text
1. User invokes: invoice-gen --partner ubereats --count 5 --gcs-bucket invoices-input-dev
   │
   ▼
2. CLI validates GCS access (creates GCSUploader, checks bucket exists)
   │ → If fails: Exit with clear error message
   ▼
3. InvoiceGenerator generates 5 TIFF files locally
   │ → Progress bar: "Generating invoices [5/5]"
   ▼
4. For each generated file, GCSUploader.upload_file()
   │ → Progress bar: "Uploading to GCS [5/5]"
   │ → On failure: Log warning, continue
   ▼
5. Report summary:
   │ → Success: "☁️ Uploaded: 5/5 files to gs://invoices-input-dev/"
   │ → Partial: "☁️ Uploaded: 4/5 files (1 failed)"
   ▼
6. Exit code: 0 if all successful, 1 if any failures
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|-----------------|----------------|
| Google Cloud Storage | Python SDK (`google-cloud-storage`) | ADC (Application Default Credentials) |

**ADC Resolution Order:**
1. `GOOGLE_APPLICATION_CREDENTIALS` environment variable
2. `gcloud auth application-default login` credentials
3. Service account attached to compute instance (when on GCP)

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|---------------|
| Unit | GCSUploader class | `test_gcs_uploader.py` | pytest + mocks | 90% |
| Unit | CLI flag parsing | `test_cli.py` | pytest + CliRunner | 90% |
| Integration | End-to-end with real GCS | Manual | Real bucket | Happy path |

**Test Matrix:**

| Test ID | Scenario | Mock/Real | Acceptance Test |
|---------|----------|-----------|-----------------|
| T-001 | Bucket validation on init | Mock | AT-005 |
| T-002 | Upload single file success | Mock | AT-001 |
| T-003 | Upload failure handling | Mock | AT-003 |
| T-004 | CLI without --gcs-bucket | CliRunner | AT-002 |
| T-005 | CLI with --gcs-bucket | CliRunner + Mock | AT-001 |
| T-006 | Invalid bucket error | Mock | AT-004 |

---

## Error Handling

| Error Type | Handling Strategy | Retry? | Exit Code |
|------------|-------------------|--------|-----------|
| Missing ADC credentials | Fail fast with clear message | No | 1 |
| Bucket not found | Fail fast with clear message | No | 1 |
| Single file upload failure | Warn, continue, report at end | No | 1 |
| Network timeout | Treated as upload failure | No | 1 |
| Permission denied | Treated as upload failure | No | 1 |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `--gcs-bucket` | string | `None` | Target GCS bucket (optional) |

**No additional configuration required** — ADC handles authentication automatically.

---

## Security Considerations

- **ADC Only:** No credential files stored in code or repo
- **Bucket Validation:** Verifies access before processing
- **No Secrets in Logs:** Error messages don't expose credentials
- **Principle of Least Privilege:** Only `storage.objects.create` permission needed

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| Logging | CLI output via `click.echo()` with colored warnings |
| Metrics | Upload count reported at end (success/failed) |
| Tracing | Not required (simple CLI tool) |

---

## Dependencies

**New dependency to add to `pyproject.toml`:**

```toml
[project]
dependencies = [
    # ... existing ...
    "google-cloud-storage>=2.10.0",
]
```

**Why 2.10.0+:**
- Stable ADC support
- `upload_from_filename` with timeout parameter
- Python 3.11+ compatibility

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-30 | design-agent | Initial version |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_GCS_UPLOAD.md`
