"""Pydantic models for smoke test results and context."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


@dataclass
class SmokeContext:
    """Mutable context passed between stages.

    This dataclass accumulates data as stages execute, allowing each stage
    to access outputs from previous stages.
    """

    env: str = "dev"
    vendor: str = "ubereats"
    invoice_data: Any = None
    tiff_path: Path | None = None
    gcs_object_path: str | None = None
    extracted_json_path: str | None = None
    extracted_data: dict | None = None
    validation_passed: bool = False
    field_mismatches: list[str] = field(default_factory=list)
    bq_row_found: bool = False
    log_errors_found: list[str] = field(default_factory=list)


class SmokeResult(BaseModel):
    """Final smoke test result with all stage outcomes."""

    success: bool = Field(description="True if all stages passed")
    env: str = Field(description="Environment tested (dev/prod)")
    vendor: str = Field(description="Vendor type tested")
    total_duration_ms: int = Field(description="Total test duration in ms")
    stages: list[dict] = Field(default_factory=list, description="Per-stage results")
    stages_passed: int = Field(default=0)
    stages_failed: int = Field(default=0)
    stages_skipped: int = Field(default=0)
    invoice_id: str | None = Field(default=None)
    error_summary: str | None = Field(default=None)
