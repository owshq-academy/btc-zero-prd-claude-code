"""Cloud Run entry point for DLQ processor.

Triggered by Pub/Sub messages on dead-letter queue topics.
Captures failed messages, creates error files in the failed bucket,
and provides observability for pipeline failures.
"""

import base64
import json
import logging
from datetime import datetime, timezone

import functions_framework
from cloudevents.http import CloudEvent

from shared.adapters import GCSAdapter
from shared.utils import configure_logging, get_config

from .processor import create_error_record, write_error_to_gcs

configure_logging()
logger = logging.getLogger(__name__)


@functions_framework.cloud_event
def handle_dlq_message(cloud_event: CloudEvent) -> None:
    """Cloud Run entry point - triggered by DLQ Pub/Sub topics.

    Processes failed messages by:
    1. Extracting the original message and error details
    2. Creating a structured error record
    3. Writing to the failed bucket with .error.json suffix
    4. Logging for observability

    Args:
        cloud_event: CloudEvent containing failed Pub/Sub message with:
            - Original message data
            - Delivery attempt count
            - Subscription info

    Note:
        This function should NOT raise exceptions to avoid infinite DLQ loops.
        All errors are logged but the message is acknowledged.
    """
    config = get_config()
    storage = GCSAdapter(project_id=config.project_id)

    try:
        message_data = cloud_event.data.get("message", {})
        raw_data = message_data.get("data", "")

        if raw_data:
            decoded_data = base64.b64decode(raw_data)
            original_message = json.loads(decoded_data)
        else:
            original_message = {}

        attributes = message_data.get("attributes", {})
        subscription = cloud_event.data.get("subscription", "unknown")
        message_id = message_data.get("messageId", "unknown")

        source_file = original_message.get("source_file", "unknown")
        invoice_id = original_message.get("invoice_id")
        if not invoice_id and "extracted_data" in original_message:
            invoice_id = original_message["extracted_data"].get("invoice_id")
        invoice_id = invoice_id or "unknown"

        dlq_topic = _extract_dlq_topic(subscription)

        logger.info(
            "Processing DLQ message",
            extra={
                "message_id": message_id,
                "dlq_topic": dlq_topic,
                "source_file": source_file,
                "invoice_id": invoice_id,
            },
        )

        error_record = create_error_record(
            original_message=original_message,
            dlq_topic=dlq_topic,
            message_id=message_id,
            subscription=subscription,
            attributes=attributes,
            timestamp=datetime.now(timezone.utc),
        )

        error_path = write_error_to_gcs(
            storage=storage,
            bucket=config.failed_bucket,
            source_file=source_file,
            invoice_id=invoice_id,
            error_record=error_record,
        )

        logger.info(
            "DLQ message processed - error file created",
            extra={
                "error_path": error_path,
                "invoice_id": invoice_id,
                "dlq_topic": dlq_topic,
            },
        )

    except Exception as e:
        logger.exception(
            "DLQ processor error - message will be acknowledged to prevent loop",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )


def _extract_dlq_topic(subscription: str) -> str:
    """Extract DLQ topic name from subscription path."""
    if "invoice-extracted-dlq" in subscription:
        return "invoice-extracted-dlq"
    elif "invoice-classified-dlq" in subscription:
        return "invoice-classified-dlq"
    elif "invoice-converted-dlq" in subscription:
        return "invoice-converted-dlq"
    elif "invoice-uploaded-dlq" in subscription:
        return "invoice-uploaded-dlq"
    return "unknown-dlq"
