"""Cloud Run entry point for data extractor.

Triggered by Pub/Sub messages on the invoice-classified topic.
Downloads images, extracts data using Gemini, validates with Pydantic,
and publishes extraction results to invoice-extracted topic.

Supports LangFuse integration for:
- End-to-end distributed tracing across pipeline functions
- Prompt Management with versioned prompts
- LLM observability with token tracking and confidence scoring
"""

import base64
import json
import logging

import functions_framework
from cloudevents.http import CloudEvent

from shared.adapters import (
    GCSAdapter,
    GeminiAdapter,
    PubSubAdapter,
    TraceContext,
    create_observer,
)
from shared.adapters.llm import OpenRouterAdapter
from shared.schemas.messages import InvoiceClassifiedMessage, InvoiceExtractedMessage
from shared.utils import configure_logging, function_timer, get_config, parse_gcs_uri

from .extractor import (
    calculate_extraction_scores,
    extract_invoice,
    get_score_comments,
)

configure_logging()
logger = logging.getLogger(__name__)


@functions_framework.cloud_event
def handle_invoice_classified(cloud_event: CloudEvent) -> None:
    """Cloud Run entry point - triggered by Pub/Sub.

    Processes classified invoices by:
    1. Downloading PNG(s) from processed bucket
    2. Loading vendor-specific prompt template
    3. Calling Gemini 2.5 Flash for extraction
    4. Validating response with Pydantic
    5. Falling back to OpenRouter on failure
    6. Publishing extracted data or moving to failed bucket

    Args:
        cloud_event: CloudEvent containing Pub/Sub message with:
            - source_file: GCS URI of original TIFF
            - converted_files: List of GCS URIs for PNGs
            - vendor_type: Detected vendor type
            - quality_score: Image quality score

    Raises:
        Exception: Re-raised to trigger Cloud Run retry on failure
    """
    config = get_config()
    storage = GCSAdapter(project_id=config.project_id)
    messaging = PubSubAdapter(project_id=config.project_id)

    observer = create_observer(enabled=config.langfuse_enabled)

    gemini = GeminiAdapter(
        project_id=config.project_id,
        region=config.region,
        model=config.gemini_model,
        observer=observer,
    )

    openrouter = None
    if config.openrouter_api_key:
        openrouter = OpenRouterAdapter(
            api_key=config.openrouter_api_key,
            observer=observer,
        )

    source_file = "unknown"
    total_input_bytes = 0
    exception_to_raise: Exception | None = None
    result = None
    trace_context = None
    message = None

    with function_timer() as timing:
        try:
            message_data = base64.b64decode(cloud_event.data["message"]["data"])
            raw_message = json.loads(message_data)

            message = InvoiceClassifiedMessage.model_validate(raw_message)
            source_file = message.source_file

            trace_context = TraceContext.from_message(message)

            logger.info(
                "Processing classified invoice",
                extra={
                    "source_file": source_file,
                    "vendor_type": message.vendor_type.value,
                    "quality_score": message.quality_score,
                    "page_count": len(message.converted_files),
                    "trace_id": trace_context.trace_id,
                    "session_id": trace_context.session_id,
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

            result = extract_invoice(
                images_data=images_data,
                vendor_type=message.vendor_type,
                llm_adapter=gemini,
                fallback_adapter=openrouter,
                observer=observer,
            )

            if not result.success:
                logger.error(
                    "Extraction failed - moving to failed bucket",
                    extra={
                        "source_file": source_file,
                        "error": result.error,
                        "provider": result.provider,
                        "llm_latency_ms": result.latency_ms,
                    },
                )

                _copy_to_failed_bucket(storage, config, source_file, result.error or "Unknown error")
                observer.flush()
                return

            logger.info(
                "Extraction successful",
                extra={
                    "source_file": source_file,
                    "vendor_type": message.vendor_type.value,
                    "provider": result.provider,
                    "llm_latency_ms": result.latency_ms,
                    "confidence": result.confidence,
                    "invoice_id": result.invoice.invoice_id if result.invoice else None,
                    "prompt_name": result.prompt_name,
                    "prompt_version": result.prompt_version,
                    "trace_id": trace_context.trace_id,
                },
            )

            if result.invoice and observer.is_enabled:
                extraction_scores = calculate_extraction_scores(result.invoice)
                extraction_scores["extraction_confidence"] = result.confidence
                score_comments = get_score_comments(result.invoice, extraction_scores)
                score_comments["extraction_confidence"] = (
                    f"Provider: {result.provider}, latency: {result.latency_ms}ms"
                )

                observer.score_trace(
                    trace_id=trace_context.trace_id,
                    scores=extraction_scores,
                    comments=score_comments,
                )

                logger.debug(
                    "Added LangFuse scores",
                    extra={
                        "trace_id": trace_context.trace_id,
                        "scores": extraction_scores,
                    },
                )

            extracted_message = InvoiceExtractedMessage(
                trace_id=trace_context.trace_id,
                session_id=trace_context.session_id,
                parent_span_id=trace_context.parent_span_id,
                source_file=source_file,
                vendor_type=message.vendor_type,
                extraction_model="gemini-2.5-flash" if result.provider == "gemini" else "openrouter",
                extraction_latency_ms=result.latency_ms,
                confidence_score=result.confidence,
                extracted_data=result.invoice.model_dump(mode="json") if result.invoice else {},
                prompt_name=result.prompt_name,
                prompt_version=result.prompt_version,
            )

            messaging.publish(
                config.extracted_topic,
                extracted_message.model_dump(mode="json"),
            )

            observer.flush()

        except Exception as e:
            exception_to_raise = e
            observer.flush()

    if exception_to_raise:
        logger.exception(
            "Extraction processing failed",
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
        "Extraction complete - published event",
        extra={
            "source_file": source_file,
            "invoice_id": result.invoice.invoice_id if result and result.invoice else None,
            "topic": config.extracted_topic,
            "latency_ms": timing["latency_ms"],
            "llm_latency_ms": result.latency_ms if result else 0,
            "total_input_bytes": total_input_bytes,
        },
    )


def _copy_to_failed_bucket(
    storage: GCSAdapter,
    config,
    source_file: str,
    error_message: str,
) -> None:
    """Copy failed invoice to failed bucket with error metadata.

    Files are flattened to the bucket root for simpler agentic monitoring.

    Args:
        storage: GCS adapter
        config: Application configuration
        source_file: Source file GCS URI
        error_message: Error description
    """
    try:
        source_bucket, source_path = parse_gcs_uri(source_file)

        filename = source_path.split("/")[-1]

        storage.copy(
            source_bucket,
            source_path,
            config.failed_bucket,
            filename,
        )

        error_path = f"{filename}.error.json"
        error_data = json.dumps({
            "source_file": source_file,
            "error": error_message,
        }).encode()

        storage.write(
            config.failed_bucket,
            error_path,
            error_data,
            "application/json",
        )

        logger.info(
            "Copied failed invoice to failed bucket",
            extra={
                "source_file": source_file,
                "failed_uri": f"gs://{config.failed_bucket}/{filename}",
            },
        )

    except Exception as e:
        logger.error(
            "Failed to copy to failed bucket",
            extra={
                "source_file": source_file,
                "error": str(e),
            },
        )
