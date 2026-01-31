"""Pub/Sub message schemas for pipeline events.

Each function in the pipeline publishes messages to the next stage.
These Pydantic models define the contract between functions.

All messages include trace context for end-to-end LangFuse observability.
"""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from shared.schemas.invoice import VendorType


def generate_trace_id() -> str:
    """Generate a W3C-compliant trace ID (32 hex chars)."""
    return uuid.uuid4().hex


def generate_span_id() -> str:
    """Generate a W3C-compliant span ID (16 hex chars)."""
    return uuid.uuid4().hex[:16]


class TraceContextMixin(BaseModel):
    """Mixin for distributed tracing context propagation.

    All pipeline messages include these fields to enable end-to-end
    tracing in LangFuse across all 4 Cloud Run functions.
    """

    trace_id: str = Field(
        default_factory=generate_trace_id,
        description="W3C trace ID (32 hex chars) - shared across entire pipeline",
        min_length=32,
        max_length=32,
    )
    session_id: str | None = Field(
        default=None,
        description="LangFuse session ID for grouping related invoices",
    )
    parent_span_id: str | None = Field(
        default=None,
        description="W3C span ID (16 hex chars) of the parent span",
    )


class InvoiceUploadedMessage(TraceContextMixin):
    """Message published when TIFF lands in input bucket (GCS notification)."""

    bucket: str = Field(..., description="GCS bucket name")
    name: str = Field(..., description="File path in bucket")
    event_time: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")


class InvoiceConvertedMessage(TraceContextMixin):
    """Message published after TIFF to PNG conversion."""

    source_file: str = Field(..., description="gs:// URI of original TIFF")
    converted_files: list[str] = Field(..., description="List of gs:// URIs for PNGs")
    page_count: int = Field(..., ge=1, description="Number of pages converted")
    event_time: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")


class InvoiceClassifiedMessage(TraceContextMixin):
    """Message published after vendor classification."""

    source_file: str = Field(..., description="gs:// URI of original TIFF")
    converted_files: list[str] = Field(..., description="List of gs:// URIs for PNGs")
    vendor_type: VendorType = Field(..., description="Detected vendor type")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Image quality score")
    archived_to: str = Field(..., description="gs:// URI in archive bucket")
    event_time: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")


class InvoiceExtractedMessage(TraceContextMixin):
    """Message published after LLM extraction."""

    source_file: str = Field(..., description="gs:// URI of original TIFF")
    vendor_type: VendorType = Field(..., description="Vendor type")
    extraction_model: Literal["gemini-2.5-flash", "openrouter"] = Field(
        ..., description="Model used for extraction"
    )
    extraction_latency_ms: int = Field(..., ge=0, description="Extraction latency")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    extracted_data: dict[str, Any] = Field(..., description="ExtractedInvoice as dict")
    prompt_name: str | None = Field(
        default=None, description="LangFuse prompt name used for extraction"
    )
    prompt_version: int | None = Field(
        default=None, description="LangFuse prompt version used"
    )
    event_time: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
