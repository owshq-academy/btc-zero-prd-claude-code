"""Cloud Run entry point for TIFF-to-PNG converter.

Triggered by Pub/Sub messages on the invoice-uploaded topic.
Downloads TIFF from GCS, converts to PNG(s), uploads to processed bucket,
and publishes completion event to invoice-converted topic.
"""

import base64
import json
import logging

import functions_framework
from cloudevents.http import CloudEvent

from shared.adapters import GCSAdapter, PubSubAdapter
from shared.schemas.messages import InvoiceConvertedMessage, InvoiceUploadedMessage
from shared.utils import configure_logging, function_timer, get_config

from .converter import convert_tiff_to_png_detailed

configure_logging()
logger = logging.getLogger(__name__)


@functions_framework.cloud_event
def handle_invoice_uploaded(cloud_event: CloudEvent) -> None:
    """Cloud Run entry point - triggered by Pub/Sub.

    Processes TIFF invoice uploads by:
    1. Downloading TIFF from input bucket
    2. Converting to PNG (handles multi-page)
    3. Uploading PNG(s) to processed bucket
    4. Publishing completion event

    Args:
        cloud_event: CloudEvent containing Pub/Sub message with:
            - bucket: GCS bucket name
            - name: File path in bucket

    Raises:
        Exception: Re-raised to trigger Cloud Run retry on failure
    """
    config = get_config()
    storage = GCSAdapter(project_id=config.project_id)
    messaging = PubSubAdapter(project_id=config.project_id)

    file_path = "unknown"
    input_size_bytes = 0
    total_output_bytes = 0
    exception_to_raise: Exception | None = None

    with function_timer() as timing:
        try:
            message_data = base64.b64decode(cloud_event.data["message"]["data"])
            raw_message = json.loads(message_data)

            message = InvoiceUploadedMessage.model_validate(raw_message)
            file_path = message.name

            logger.info(
                "Processing invoice upload",
                extra={
                    "bucket": message.bucket,
                    "file_path": file_path,
                    "event_time": message.event_time.isoformat(),
                },
            )

            if not _is_tiff_file(file_path):
                logger.warning(
                    "Skipping non-TIFF file",
                    extra={"file_path": file_path},
                )
                return

            tiff_data = storage.read(message.bucket, file_path)
            input_size_bytes = len(tiff_data)

            logger.info(
                "Downloaded TIFF file",
                extra={
                    "file_path": file_path,
                    "input_size_bytes": input_size_bytes,
                },
            )

            result = convert_tiff_to_png_detailed(tiff_data)

            logger.info(
                "Converted TIFF to PNG",
                extra={
                    "file_path": file_path,
                    "page_count": result.page_count,
                    "input_size_bytes": result.original_size_bytes,
                    "total_output_bytes": result.total_output_bytes,
                },
            )

            converted_uris: list[str] = []
            base_name = file_path.rsplit(".", 1)[0]
            total_output_bytes = 0

            for i, png_data in enumerate(result.pages):
                png_path = f"{base_name}_page{i + 1}.png"
                uri = storage.write(
                    config.processed_bucket,
                    png_path,
                    png_data,
                    "image/png",
                )
                converted_uris.append(uri)
                total_output_bytes += len(png_data)

                logger.debug(
                    "Uploaded PNG page",
                    extra={
                        "page": i + 1,
                        "uri": uri,
                        "output_size_bytes": len(png_data),
                    },
                )

            converted_message = InvoiceConvertedMessage(
                source_file=f"gs://{message.bucket}/{file_path}",
                converted_files=converted_uris,
                page_count=result.page_count,
            )

            messaging.publish(
                config.converted_topic,
                converted_message.model_dump(mode="json"),
            )

        except Exception as e:
            exception_to_raise = e

    if exception_to_raise:
        logger.exception(
            "Conversion failed",
            extra={
                "error": str(exception_to_raise),
                "error_type": type(exception_to_raise).__name__,
                "file_path": file_path,
                "latency_ms": timing["latency_ms"],
                "input_size_bytes": input_size_bytes,
            },
            exc_info=exception_to_raise,
        )
        raise exception_to_raise

    logger.info(
        "Conversion complete - published event",
        extra={
            "source_file": file_path,
            "page_count": result.page_count,
            "converted_files": converted_uris,
            "topic": config.converted_topic,
            "latency_ms": timing["latency_ms"],
            "input_size_bytes": input_size_bytes,
            "total_output_bytes": total_output_bytes,
        },
    )


def _is_tiff_file(file_path: str) -> bool:
    """Check if file has TIFF extension.

    Args:
        file_path: File path to check

    Returns:
        True if file has .tiff or .tif extension (case-insensitive)
    """
    lower_path = file_path.lower()
    return lower_path.endswith(".tiff") or lower_path.endswith(".tif")
