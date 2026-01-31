"""Cloud Run entry point for invoice classifier.

Triggered by Pub/Sub messages on the invoice-converted topic.
Validates image quality, detects vendor type, archives originals,
and publishes classification results to invoice-classified topic.
"""

import base64
import json
import logging

import functions_framework
from cloudevents.http import CloudEvent

from shared.adapters import GCSAdapter, PubSubAdapter
from shared.schemas.messages import InvoiceClassifiedMessage, InvoiceConvertedMessage
from shared.utils import configure_logging, function_timer, get_config, parse_gcs_uri

from .classifier import classify_vendor, validate_all_images

configure_logging()
logger = logging.getLogger(__name__)


@functions_framework.cloud_event
def handle_invoice_converted(cloud_event: CloudEvent) -> None:
    """Cloud Run entry point - triggered by Pub/Sub.

    Processes converted invoices by:
    1. Downloading PNG(s) from processed bucket
    2. Validating image quality
    3. Classifying vendor type from filename patterns
    4. Archiving original TIFF to archive bucket
    5. Publishing classification results

    Args:
        cloud_event: CloudEvent containing Pub/Sub message with:
            - source_file: GCS URI of original TIFF
            - converted_files: List of GCS URIs for PNGs
            - page_count: Number of pages

    Raises:
        Exception: Re-raised to trigger Cloud Run retry on failure
    """
    config = get_config()
    storage = GCSAdapter(project_id=config.project_id)
    messaging = PubSubAdapter(project_id=config.project_id)

    source_file = "unknown"
    total_input_bytes = 0
    exception_to_raise: Exception | None = None
    classification = None
    avg_score = 0.0

    with function_timer() as timing:
        try:
            message_data = base64.b64decode(cloud_event.data["message"]["data"])
            raw_message = json.loads(message_data)

            message = InvoiceConvertedMessage.model_validate(raw_message)
            source_file = message.source_file

            logger.info(
                "Processing converted invoice",
                extra={
                    "source_file": source_file,
                    "page_count": message.page_count,
                    "converted_files": message.converted_files,
                },
            )

            images_data = []
            total_input_bytes = 0
            for png_uri in message.converted_files:
                bucket, path = parse_gcs_uri(png_uri)
                png_data = storage.read(bucket, path)
                images_data.append(png_data)
                total_input_bytes += len(png_data)

            logger.info(
                "Downloaded all images",
                extra={
                    "source_file": source_file,
                    "file_count": len(images_data),
                    "total_input_bytes": total_input_bytes,
                },
            )

            all_valid, avg_score, issues = validate_all_images(images_data)

            if not all_valid:
                logger.warning(
                    "Image quality validation failed",
                    extra={
                        "source_file": source_file,
                        "quality_score": avg_score,
                        "issues": issues,
                    },
                )

            classification = classify_vendor(source_file, message.converted_files)

            logger.info(
                "Vendor classification complete",
                extra={
                    "source_file": source_file,
                    "vendor_type": classification.vendor_type.value,
                    "confidence": classification.confidence,
                    "detection_method": classification.detection_method,
                    "matched_pattern": classification.matched_pattern,
                },
            )

            source_bucket, source_path = parse_gcs_uri(source_file)
            archive_path = source_path
            archive_uri = storage.copy(
                source_bucket,
                source_path,
                config.archive_bucket,
                archive_path,
            )

            logger.info(
                "Archived original file",
                extra={
                    "source_file": source_file,
                    "archive_uri": archive_uri,
                },
            )

            classified_message = InvoiceClassifiedMessage(
                source_file=source_file,
                converted_files=message.converted_files,
                vendor_type=classification.vendor_type,
                quality_score=avg_score,
                archived_to=archive_uri,
            )

            messaging.publish(
                config.classified_topic,
                classified_message.model_dump(mode="json"),
            )

        except Exception as e:
            exception_to_raise = e

    if exception_to_raise:
        logger.exception(
            "Classification failed",
            extra={
                "error": str(exception_to_raise),
                "error_type": type(exception_to_raise).__name__,
                "source_file": source_file,
                "latency_ms": timing["latency_ms"],
                "total_input_bytes": total_input_bytes,
            },
            exc_info=exception_to_raise,
        )
        raise exception_to_raise

    logger.info(
        "Classification complete - published event",
        extra={
            "source_file": source_file,
            "vendor_type": classification.vendor_type.value if classification else "unknown",
            "quality_score": avg_score,
            "topic": config.classified_topic,
            "latency_ms": timing["latency_ms"],
            "total_input_bytes": total_input_bytes,
        },
    )
