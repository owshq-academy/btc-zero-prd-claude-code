# BUILD Report: Smoke Test Framework

**Feature:** End-to-End Smoke Test Framework
**Date:** 2026-01-30
**Status:** ✅ Complete

---

## Summary

Successfully implemented a complete end-to-end smoke test framework for the invoice processing pipeline. The framework validates the entire flow from invoice generation through BigQuery output, with fail-fast execution and structured result reporting.

---

## Files Created

| File | Purpose |
|------|---------|
| `tests/__init__.py` | Test suite root package |
| `tests/smoke/__init__.py` | Smoke test package |
| `tests/smoke/models.py` | SmokeContext and SmokeResult dataclasses/models |
| `tests/smoke/config.py` | YAML configuration loader with Pydantic models |
| `tests/smoke/config/smoke_config.yaml` | Environment and stage configuration |
| `tests/smoke/stages/__init__.py` | Stage package with exports |
| `tests/smoke/stages/base.py` | ABC Stage class with timing wrapper |
| `tests/smoke/stages/generate.py` | Stage 1: Generate invoice via invoice-gen |
| `tests/smoke/stages/upload.py` | Stage 2: Upload TIFF to GCS |
| `tests/smoke/stages/process.py` | Stage 3: Poll GCS for extraction |
| `tests/smoke/stages/validate.py` | Stage 4: Field validation |
| `tests/smoke/stages/bigquery.py` | Stage 5: Query BigQuery |
| `tests/smoke/stages/logging.py` | Stage 6: Check Cloud Logging |
| `tests/smoke/validators/__init__.py` | Validator package |
| `tests/smoke/validators/field_matcher.py` | Field matching with normalization |
| `tests/smoke/runner.py` | Stage orchestrator with fail-fast |
| `tests/smoke/cli.py` | Click CLI entry point |
| `tests/smoke/pyproject.toml` | Package configuration |
| `tests/smoke/fixtures/.gitkeep` | Fixtures placeholder |

**Total:** 19 files created

---

## Architecture Decisions Implemented

### ADR-1: Stage-Based Pipeline
- Implemented ABC `Stage` class with `run()` and `execute()` methods
- Each stage is independent and receives shared `SmokeContext`
- Automatic timing and error handling via Template Method pattern

### ADR-2: Fail-Fast Execution
- Runner stops at first failure when `--fail-fast` is enabled
- Remaining stages marked as "skipped" in results
- Exit code 1 on any failure

### ADR-3: Ground Truth from invoice-gen
- `GenerateStage` imports `InvoiceGenerator` directly as library
- `invoice_data` stored in context serves as validation ground truth
- No file parsing needed - structured data available immediately

### ADR-4: Field Matching with Normalization
- Critical fields: `invoice_id`, `vendor_type`, `total_amount`, `currency`
- Type normalization: Decimal→float, string→float where applicable
- Case-insensitive vendor comparison

### ADR-5: Click CLI
- Single `smoke-test` command with options
- Supports `--env`, `--vendor`, `--fail-fast`, `--json-output`
- Human-readable and JSON output modes

---

## Verification Results

| Check | Status |
|-------|--------|
| Python syntax (all 16 .py files) | ✅ Pass |
| Module imports | ✅ Pass |
| Config loading | ✅ Pass |
| Field matching normalization | ✅ Pass |
| CLI help display | ✅ Pass |

---

## Usage Examples

```bash
# Run smoke test (default: dev + ubereats)
python -m tests.smoke.cli

# Test specific vendor in prod
python -m tests.smoke.cli --env prod --vendor doordash

# Skip Cloud Logging check
python -m tests.smoke.cli --skip-logging

# JSON output for CI/CD integration
python -m tests.smoke.cli --json-output

# Run all stages even on failure
python -m tests.smoke.cli --no-fail-fast
```

---

## Dependencies Required

```
click>=8.1.0
pydantic>=2.0.0
pyyaml>=6.0.0
google-cloud-storage>=2.0.0
google-cloud-bigquery>=3.0.0
google-cloud-logging>=3.0.0
invoice-gen  # Local: pip install -e gen/synthetic-invoice-gen
```

---

## Notes

1. **CI/CD Integration**: Deferred to future iteration as requested
2. **invoice-gen**: Must be installed from local path for GenerateStage to work
3. **GCP Credentials**: Requires Application Default Credentials configured
4. **Timeouts**: Configurable in `smoke_config.yaml` (default: 60s for processing)

---

## Next Steps (Future Iterations)

- [ ] Add CI/CD pipeline integration (Azure DevOps)
- [ ] Implement LangFuse trace validation stage
- [ ] Add HTML report generation
- [ ] Support parallel multi-vendor testing
