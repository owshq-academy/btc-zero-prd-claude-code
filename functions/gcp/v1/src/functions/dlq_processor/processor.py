"""DLQ processor logic for creating error records and writing to GCS."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from shared.adapters.storage import GCSAdapter


def create_error_record(
    original_message: dict[str, Any],
    dlq_topic: str,
    message_id: str,
    subscription: str,
    attributes: dict[str, str],
    timestamp: datetime,
) -> dict[str, Any]:
    """Create a structured error record from a failed message.

    Args:
        original_message: The original Pub/Sub message payload
        dlq_topic: Which DLQ topic received the message
        message_id: Pub/Sub message ID
        subscription: Subscription that delivered the message
        attributes: Pub/Sub message attributes
        timestamp: When the error was processed

    Returns:
        Structured error record ready for JSON serialization
    """
    source_file = original_message.get("source_file", "unknown")
    vendor_type = original_message.get("vendor_type", "unknown")

    invoice_id = original_message.get("invoice_id")
    if not invoice_id and "extracted_data" in original_message:
        invoice_id = original_message["extracted_data"].get("invoice_id")

    stage = _determine_failed_stage(dlq_topic)

    return {
        "error_metadata": {
            "timestamp": timestamp.isoformat(),
            "dlq_topic": dlq_topic,
            "message_id": message_id,
            "subscription": subscription,
            "failed_stage": stage,
        },
        "invoice_context": {
            "source_file": source_file,
            "invoice_id": invoice_id,
            "vendor_type": vendor_type,
        },
        "original_message": original_message,
        "attributes": attributes,
    }


def write_error_to_gcs(
    storage: GCSAdapter,
    bucket: str,
    source_file: str,
    invoice_id: str,
    error_record: dict[str, Any],
) -> str:
    """Write error record to GCS failed bucket.

    Args:
        storage: GCS storage adapter
        bucket: Failed bucket name
        source_file: Original source file path
        invoice_id: Invoice ID if available
        error_record: Structured error record

    Returns:
        GCS URI of the created error file
    """
    error_filename = _generate_error_filename(source_file, invoice_id)
    error_json = json.dumps(error_record, indent=2, default=str)

    gcs_uri = storage.write(
        bucket=bucket,
        path=error_filename,
        data=error_json.encode("utf-8"),
        content_type="application/json",
    )

    return gcs_uri


def _determine_failed_stage(dlq_topic: str) -> str:
    """Determine which pipeline stage failed based on DLQ topic."""
    stage_map = {
        "invoice-uploaded-dlq": "tiff-to-png-converter",
        "invoice-converted-dlq": "invoice-classifier",
        "invoice-classified-dlq": "data-extractor",
        "invoice-extracted-dlq": "bigquery-writer",
    }
    return stage_map.get(dlq_topic, "unknown")


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
