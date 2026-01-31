"""Cloud Run entry point for BigQuery writer.

Triggered by Pub/Sub messages on the invoice-extracted topic.
Validates extracted data, checks for duplicates, writes to BigQuery,
and logs extraction metrics.

Failed invoices are written to the failed bucket with structured error
files for downstream agentic processing.
"""

import base64
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import functions_framework
from cloudevents.http import CloudEvent
from pydantic import ValidationError

from shared.adapters import GCPBigQueryAdapter, GCSAdapter, PubSubAdapter
from shared.schemas.invoice import ExtractedInvoice
from shared.schemas.messages import InvoiceExtractedMessage
from shared.utils import configure_logging, function_timer, get_config

from .writer import write_extraction_metrics, write_invoice_to_bigquery

configure_logging()
logger = logging.getLogger(__name__)


@functions_framework.cloud_event
def handle_invoice_extracted(cloud_event: CloudEvent) -> None:
    """Cloud Run entry point - triggered by Pub/Sub.

    Processes extracted invoices by:
    1. Re-validating extracted data with Pydantic (defense in depth)
    2. Checking for duplicate invoices
    3. Writing invoice and line items to BigQuery
    4. Logging extraction metrics

    On failure:
    - Writes structured error file to failed bucket for agentic processing
    - Acknowledges the message (does NOT re-raise to prevent infinite retries)
    - Error files include remediation hints for AI agents

    Args:
        cloud_event: CloudEvent containing Pub/Sub message with:
            - source_file: GCS URI of original file
            - vendor_type: Detected vendor type
            - extraction_model: LLM model used
            - extraction_latency_ms: Processing time
            - confidence_score: Extraction confidence
            - extracted_data: Invoice data as dict

    Note:
        This function does NOT raise exceptions to avoid Pub/Sub infinite retries.
        All failures are captured in the failed bucket for downstream processing.
    """
    config = get_config()
    bq_adapter = GCPBigQueryAdapter(project_id=config.project_id)

    source_file = "unknown"
    invoice_id = "unknown"
    success = False
    result = None
    invoice = None
    message = None
    raw_message = {}

    with function_timer() as timing:
        try:
            message_data = base64.b64decode(cloud_event.data["message"]["data"])
            raw_message = json.loads(message_data)

            message = InvoiceExtractedMessage.model_validate(raw_message)
            source_file = message.source_file

            logger.info(
                "Processing extracted invoice",
                extra={
                    "source_file": source_file,
                    "vendor_type": message.vendor_type.value,
                    "extraction_model": message.extraction_model,
                    "confidence_score": message.confidence_score,
                },
            )

            invoice = ExtractedInvoice.model_validate(message.extracted_data)
            invoice_id = invoice.invoice_id

            logger.info(
                "Invoice re-validated successfully",
                extra={
                    "invoice_id": invoice_id,
                    "vendor_type": invoice.vendor_type.value,
                    "line_items_count": len(invoice.line_items),
                    "total_amount": str(invoice.total_amount),
                },
            )

            result = write_invoice_to_bigquery(
                invoice=invoice,
                bq_adapter=bq_adapter,
                dataset=config.dataset,
                invoices_table=config.invoices_table,
                line_items_table=config.line_items_table,
                source_file=source_file,
                extraction_model=message.extraction_model,
                extraction_latency_ms=message.extraction_latency_ms,
                confidence_score=message.confidence_score,
            )

            if not result.success:
                logger.error(
                    "BigQuery write failed",
                    extra={
                        "invoice_id": invoice_id,
                        "error": result.error,
                    },
                )
                raise RuntimeError(f"BigQuery write failed: {result.error}")

            write_extraction_metrics(
                bq_adapter=bq_adapter,
                dataset=config.dataset,
                metrics_table=config.metrics_table,
                invoice_id=invoice_id,
                vendor_type=message.vendor_type,
                source_file=source_file,
                extraction_model=message.extraction_model,
                extraction_latency_ms=message.extraction_latency_ms,
                confidence_score=message.confidence_score,
                success=True,
            )

            success = True

        except Exception as e:
            logger.exception(
                "BigQuery write processing failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "source_file": source_file,
                    "invoice_id": invoice_id,
                },
            )

            try:
                write_extraction_metrics(
                    bq_adapter=bq_adapter,
                    dataset=config.dataset,
                    metrics_table=config.metrics_table,
                    invoice_id=invoice_id,
                    vendor_type=message.vendor_type if message else "other",
                    source_file=source_file,
                    extraction_model=message.extraction_model if message else "unknown",
                    extraction_latency_ms=message.extraction_latency_ms if message else 0,
                    confidence_score=0.0,
                    success=False,
                    error_message=str(e),
                )
            except Exception:
                pass

            try:
                _write_failure_to_bucket(
                    config=config,
                    source_file=source_file,
                    invoice_id=invoice_id,
                    error=e,
                    raw_message=raw_message,
                    message=message,
                )
            except Exception as write_error:
                logger.error(
                    "Failed to write error file to bucket",
                    extra={
                        "original_error": str(e),
                        "write_error": str(write_error),
                        "source_file": source_file,
                    },
                )

    if success:
        if result and result.is_duplicate:
            logger.info(
                "Duplicate invoice - no action taken",
                extra={
                    "invoice_id": invoice_id,
                    "source_file": source_file,
                    "latency_ms": timing["latency_ms"],
                },
            )
        else:
            logger.info(
                "Invoice persisted to BigQuery",
                extra={
                    "invoice_id": invoice_id,
                    "vendor_type": invoice.vendor_type.value if invoice else "unknown",
                    "rows_written": result.rows_written if result else 0,
                    "dataset": config.dataset,
                    "table": config.invoices_table,
                    "latency_ms": timing["latency_ms"],
                },
            )
    else:
        logger.info(
            "Failed invoice written to failed bucket - message acknowledged",
            extra={
                "source_file": source_file,
                "invoice_id": invoice_id,
                "failed_bucket": config.failed_bucket,
                "latency_ms": timing["latency_ms"],
            },
        )


def _write_failure_to_bucket(
    config: Any,
    source_file: str,
    invoice_id: str,
    error: Exception,
    raw_message: dict[str, Any],
    message: InvoiceExtractedMessage | None,
) -> str:
    """Write structured error record to failed bucket for agentic processing.

    Creates a JSON file with comprehensive error context that downstream
    agents can use for automated remediation or escalation.

    Args:
        config: Application configuration
        source_file: Original source file GCS URI
        invoice_id: Invoice ID if available
        error: The exception that caused the failure
        raw_message: Raw Pub/Sub message payload
        message: Parsed message if available

    Returns:
        GCS URI of the created error file
    """
    storage = GCSAdapter(project_id=config.project_id)

    timestamp = datetime.now(timezone.utc)
    error_record = _create_error_record(
        source_file=source_file,
        invoice_id=invoice_id,
        error=error,
        raw_message=raw_message,
        message=message,
        timestamp=timestamp,
    )

    error_filename = _generate_error_filename(source_file, invoice_id)
    error_json = json.dumps(error_record, indent=2, default=str)

    gcs_uri = storage.write(
        bucket=config.failed_bucket,
        path=error_filename,
        data=error_json.encode("utf-8"),
        content_type="application/json",
    )

    return gcs_uri


def _create_error_record(
    source_file: str,
    invoice_id: str,
    error: Exception,
    raw_message: dict[str, Any],
    message: InvoiceExtractedMessage | None,
    timestamp: datetime,
) -> dict[str, Any]:
    """Create structured error record for agentic processing.

    The error record follows a schema designed for AI agents to:
    1. Understand the failure context
    2. Identify root cause from validation errors
    3. Suggest or execute remediation steps

    Returns:
        Structured error record ready for JSON serialization
    """
    validation_details = None
    if isinstance(error, ValidationError):
        validation_details = {
            "error_count": error.error_count(),
            "errors": [
                {
                    "field": ".".join(str(loc) for loc in err["loc"]),
                    "type": err["type"],
                    "message": err["msg"],
                    "input": str(err.get("input", ""))[:200],
                }
                for err in error.errors()
            ],
        }

    vendor_type = "unknown"
    extraction_model = "unknown"
    confidence_score = 0.0
    extracted_data = {}

    if message:
        vendor_type = message.vendor_type.value
        extraction_model = message.extraction_model
        confidence_score = message.confidence_score
        extracted_data = message.extracted_data

    return {
        "error_metadata": {
            "timestamp": timestamp.isoformat(),
            "failed_stage": "bigquery-writer",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "is_validation_error": isinstance(error, ValidationError),
            "validation_details": validation_details,
        },
        "invoice_context": {
            "source_file": source_file,
            "invoice_id": invoice_id,
            "vendor_type": vendor_type,
            "extraction_model": extraction_model,
            "confidence_score": confidence_score,
        },
        "extracted_data": extracted_data,
        "raw_message": raw_message,
        "remediation_hints": _generate_remediation_hints(error),
    }


def _generate_remediation_hints(error: Exception) -> list[str]:
    """Generate hints for AI agents to remediate the error.

    Analyzes the error type and message to suggest specific
    remediation actions.
    """
    hints = []

    if isinstance(error, ValidationError):
        for err in error.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            error_type = err["type"]

            if "greater_than" in error_type or "less_than" in error_type:
                hints.append(
                    f"Field '{field}' has numeric constraint violation. "
                    "Check if this is a discount/credit that should be handled differently."
                )
            elif "missing" in error_type:
                hints.append(
                    f"Required field '{field}' is missing. "
                    "Review extraction prompt for this field."
                )
            elif "string_type" in error_type or "type_error" in error_type:
                hints.append(
                    f"Field '{field}' has wrong type. "
                    "Check LLM output format for this field."
                )

    if not hints:
        hints.append("Manual review required - error pattern not recognized.")

    return hints


def _generate_error_filename(source_file: str, invoice_id: str) -> str:
    """Generate error filename from source file or invoice ID.

    Examples:
        - gs://bucket/landing/ubereats_INV-UE-123.tiff
          → ubereats_INV-UE-123.error.json

        - unknown source with invoice_id INV-GH-456
          → INV-GH-456.error.json
    """
    if source_file and source_file != "unknown":
        base_name = Path(source_file).stem
        base_name = re.sub(r"_page\d+$", "", base_name)
        return f"{base_name}.error.json"

    if invoice_id and invoice_id != "unknown":
        return f"{invoice_id}.error.json"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"unknown_{timestamp}.error.json"
