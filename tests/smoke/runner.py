"""Smoke test runner - orchestrates all stages with fail-fast logic."""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from tests.smoke.models import SmokeContext, SmokeResult
from tests.smoke.stages import (
    BigQueryStage,
    GenerateStage,
    LoggingStage,
    ProcessStage,
    Stage,
    StageResult,
    UploadStage,
    ValidateStage,
)


@dataclass
class RunnerConfig:
    """Configuration for the smoke test runner."""

    fail_fast: bool = True
    skip_logging: bool = False
    verbose: bool = False


class SmokeRunner:
    """Orchestrates smoke test stages with fail-fast and reporting.

    The runner executes stages in sequence:
    1. Generate - Create synthetic invoice
    2. Upload - Upload TIFF to GCS
    3. Process - Poll for extraction completion
    4. Validate - Compare extraction vs ground truth
    5. BigQuery - Verify row in BigQuery
    6. Logging - Check for pipeline errors

    If fail_fast is enabled, the runner stops at the first failure.
    """

    def __init__(self, config: RunnerConfig | None = None):
        """Initialize the runner.

        Args:
            config: Runner configuration. Uses defaults if not provided.
        """
        self.config = config or RunnerConfig()
        self._stages: list[Stage] = []
        self._setup_stages()

    def _setup_stages(self) -> None:
        """Configure the stage pipeline."""
        self._stages = [
            GenerateStage(),
            UploadStage(),
            ProcessStage(),
            ValidateStage(),
            BigQueryStage(),
        ]

        if not self.config.skip_logging:
            self._stages.append(LoggingStage())

    def run(
        self,
        env: str = "dev",
        vendor: str = "ubereats",
        on_stage_complete: Callable[[StageResult], None] | None = None,
    ) -> SmokeResult:
        """Run all smoke test stages.

        Args:
            env: Target environment (dev, prod)
            vendor: Vendor type (ubereats, doordash, grubhub, ifood, rappi)
            on_stage_complete: Optional callback after each stage

        Returns:
            SmokeResult with overall pass/fail and stage details
        """
        context = SmokeContext(env=env, vendor=vendor)
        stage_results: list[StageResult] = []
        start_time = time.time()

        passed = 0
        failed = 0
        skipped = 0

        for stage in self._stages:
            if self.config.fail_fast and failed > 0:
                # Skip remaining stages
                skipped += 1
                stage_results.append(
                    StageResult(
                        stage_name=stage.name,
                        passed=False,
                        error="Skipped due to previous failure",
                    )
                )
                continue

            # Execute stage
            result = stage.execute(context)
            stage_results.append(result)

            if result.passed:
                passed += 1
            else:
                failed += 1

            # Callback for progress reporting
            if on_stage_complete:
                on_stage_complete(result)

        # Calculate total duration
        total_duration_ms = int((time.time() - start_time) * 1000)

        # Determine overall success
        success = failed == 0

        # Build error summary
        error_summary = None
        if not success:
            errors = [r.error for r in stage_results if r.error and "Skipped" not in r.error]
            if errors:
                error_summary = "; ".join(errors[:3])  # Limit to first 3 errors

        # Get invoice_id if available
        invoice_id = None
        if context.invoice_data:
            invoice_id = context.invoice_data.get("invoice_id")

        return SmokeResult(
            success=success,
            env=env,
            vendor=vendor,
            total_duration_ms=total_duration_ms,
            stages=[r.to_dict() for r in stage_results],
            stages_passed=passed,
            stages_failed=failed,
            stages_skipped=skipped,
            invoice_id=invoice_id,
            error_summary=error_summary,
        )


def run_smoke_test(
    env: str = "dev",
    vendor: str = "ubereats",
    fail_fast: bool = True,
    skip_logging: bool = False,
    verbose: bool = False,
    on_stage_complete: Callable[[StageResult], None] | None = None,
) -> SmokeResult:
    """Convenience function to run a smoke test.

    Args:
        env: Target environment
        vendor: Vendor type
        fail_fast: Stop on first failure
        skip_logging: Skip the Cloud Logging check
        verbose: Enable verbose output
        on_stage_complete: Callback after each stage

    Returns:
        SmokeResult with overall pass/fail status
    """
    config = RunnerConfig(
        fail_fast=fail_fast,
        skip_logging=skip_logging,
        verbose=verbose,
    )
    runner = SmokeRunner(config)
    return runner.run(env=env, vendor=vendor, on_stage_complete=on_stage_complete)
