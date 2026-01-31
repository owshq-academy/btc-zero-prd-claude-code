"""Invoice data extraction using LLM.

Orchestrates the extraction process:
1. Load vendor-specific prompt from LangFuse (with local fallback)
2. Call Gemini via Vertex AI
3. Parse and validate JSON response
4. Fallback to OpenRouter on failure

Supports LangFuse integration for:
- Prompt Management: Fetch versioned prompts from LangFuse
- Distributed Tracing: Link extraction spans to pipeline trace
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from shared.adapters.llm import LLMAdapter, LLMResponse
from shared.schemas.invoice import ExtractedInvoice, VendorType

if TYPE_CHECKING:
    from shared.adapters.observability import LangfuseObserver, PromptResult

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


@dataclass
class InvoiceExtractionResult:
    """Result of invoice extraction.

    Attributes:
        success: Whether extraction succeeded
        invoice: Extracted invoice data (if successful)
        provider: LLM provider used (gemini or openrouter)
        latency_ms: Total extraction latency in milliseconds
        confidence: Extraction confidence score
        error: Error message (if failed)
        raw_response: Raw LLM response for debugging
        prompt_name: LangFuse prompt name used (if from LangFuse)
        prompt_version: LangFuse prompt version (if from LangFuse)
    """

    success: bool
    invoice: ExtractedInvoice | None
    provider: Literal["gemini", "openrouter"]
    latency_ms: int
    confidence: float
    error: str | None = None
    raw_response: str | None = None
    prompt_name: str | None = None
    prompt_version: int | None = None


def extract_invoice(
    images_data: list[bytes],
    vendor_type: VendorType,
    llm_adapter: LLMAdapter,
    fallback_adapter: LLMAdapter | None = None,
    observer: "LangfuseObserver | None" = None,
) -> InvoiceExtractionResult:
    """Extract structured data from invoice images.

    Uses vendor-specific prompt for better accuracy. Attempts primary
    LLM first, falls back to secondary on failure.

    Supports LangFuse Prompt Management - fetches prompts from LangFuse
    with automatic fallback to local files if unavailable.

    Args:
        images_data: List of PNG image bytes (one per page)
        vendor_type: Detected vendor type for prompt selection
        llm_adapter: Primary LLM adapter (Gemini)
        fallback_adapter: Optional fallback LLM adapter (OpenRouter)
        observer: Optional LangfuseObserver for prompt management

    Returns:
        InvoiceExtractionResult with extracted invoice or error details
    """
    # Load prompt from LangFuse or local fallback
    prompt_result = load_prompt_with_langfuse(vendor_type, observer)
    prompt = prompt_result.content

    result = _try_extraction(images_data, prompt, llm_adapter, "gemini")
    if result.success:
        # Add prompt info to result
        result.prompt_name = prompt_result.name
        result.prompt_version = prompt_result.version
        return result

    logger.warning(
        "Primary extraction failed, attempting fallback",
        extra={
            "vendor_type": vendor_type.value,
            "primary_error": result.error,
        },
    )

    if fallback_adapter:
        fallback_result = _try_extraction(
            images_data, prompt, fallback_adapter, "openrouter"
        )
        if fallback_result.success:
            # Add prompt info to result
            fallback_result.prompt_name = prompt_result.name
            fallback_result.prompt_version = prompt_result.version
            return fallback_result

        return InvoiceExtractionResult(
            success=False,
            invoice=None,
            provider="openrouter",
            latency_ms=result.latency_ms + fallback_result.latency_ms,
            confidence=0.0,
            error=f"Both providers failed. Primary: {result.error}. Fallback: {fallback_result.error}",
            raw_response=fallback_result.raw_response,
            prompt_name=prompt_result.name,
            prompt_version=prompt_result.version,
        )

    # Add prompt info to failed result
    result.prompt_name = prompt_result.name
    result.prompt_version = prompt_result.version
    return result


def _try_extraction(
    images_data: list[bytes],
    prompt: str,
    llm_adapter: LLMAdapter,
    provider: Literal["gemini", "openrouter"],
) -> InvoiceExtractionResult:
    """Attempt extraction with a single LLM provider.

    Args:
        images_data: List of PNG image bytes
        prompt: Prompt template with schema
        llm_adapter: LLM adapter to use
        provider: Provider name for logging

    Returns:
        InvoiceExtractionResult with outcome
    """
    try:
        response: LLMResponse = llm_adapter.extract(
            prompt=prompt,
            image_data=images_data,
        )

        if not response.success:
            return InvoiceExtractionResult(
                success=False,
                invoice=None,
                provider=provider,
                latency_ms=response.latency_ms,
                confidence=0.0,
                error=response.error_message or "LLM extraction failed",
                raw_response=response.content,
            )

        invoice = _parse_and_validate(response.content)

        return InvoiceExtractionResult(
            success=True,
            invoice=invoice,
            provider=provider,
            latency_ms=response.latency_ms,
            confidence=0.9,  # Default confidence for successful extractions
            raw_response=response.content,
        )

    except json.JSONDecodeError as e:
        return InvoiceExtractionResult(
            success=False,
            invoice=None,
            provider=provider,
            latency_ms=response.latency_ms if "response" in dir() else 0,
            confidence=0.0,
            error=f"JSON parse error: {e}",
            raw_response=response.content if "response" in dir() else None,
        )

    except ValueError as e:
        return InvoiceExtractionResult(
            success=False,
            invoice=None,
            provider=provider,
            latency_ms=response.latency_ms if "response" in dir() else 0,
            confidence=0.0,
            error=f"Validation error: {e}",
            raw_response=response.content if "response" in dir() else None,
        )

    except Exception as e:
        logger.exception(f"Unexpected extraction error with {provider}")
        return InvoiceExtractionResult(
            success=False,
            invoice=None,
            provider=provider,
            latency_ms=0,
            confidence=0.0,
            error=f"Unexpected error: {e}",
        )


def _parse_and_validate(content: str) -> ExtractedInvoice:
    """Parse LLM response and validate with Pydantic.

    Handles common LLM response issues:
    - Markdown code blocks (```json ... ```)
    - Leading/trailing whitespace
    - Minor JSON formatting issues

    Args:
        content: Raw LLM response text

    Returns:
        Validated ExtractedInvoice

    Raises:
        json.JSONDecodeError: If content is not valid JSON
        ValueError: If JSON doesn't match ExtractedInvoice schema
    """
    cleaned = content.strip()

    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        start_idx = 1 if lines[0].startswith("```") else 0
        end_idx = -1 if lines[-1].strip() == "```" else len(lines)
        cleaned = "\n".join(lines[start_idx:end_idx]).strip()

    data = json.loads(cleaned)

    try:
        return ExtractedInvoice.model_validate(data)
    except Exception as e:
        raise ValueError(f"Schema validation failed: {e}") from e


def load_prompt_with_langfuse(
    vendor_type: VendorType,
    observer: "LangfuseObserver | None" = None,
) -> "PromptResult":
    """Load vendor-specific prompt from LangFuse with local fallback.

    Attempts to fetch the prompt from LangFuse Prompt Management first.
    If unavailable, falls back to local prompt files.

    LangFuse prompt names follow convention: extraction-{vendor_type}
    E.g., extraction-grubhub, extraction-ubereats

    Args:
        vendor_type: Vendor type for prompt selection
        observer: Optional LangfuseObserver for prompt fetching

    Returns:
        PromptResult with prompt content and version info
    """
    from shared.adapters.observability import PromptResult

    # LangFuse prompt naming convention: extraction-{vendor}
    langfuse_prompt_name = f"extraction-{vendor_type.value}"

    # Local fallback path
    vendor_file = PROMPTS_DIR / f"{vendor_type.value}.txt"
    if not vendor_file.exists():
        vendor_file = PROMPTS_DIR / "generic.txt"

    # Get JSON schema for variable substitution
    schema = ExtractedInvoice.model_json_schema()
    schema_json = json.dumps(schema, indent=2)

    # Try LangFuse first
    if observer and observer.is_enabled:
        prompt_result = observer.get_prompt(
            name=langfuse_prompt_name,
            fallback_path=vendor_file,
            variables={"schema": schema_json},
            label="production",
        )

        if not prompt_result.is_fallback:
            logger.info(
                f"Using LangFuse prompt: {langfuse_prompt_name} v{prompt_result.version}",
                extra={
                    "prompt_name": langfuse_prompt_name,
                    "prompt_version": prompt_result.version,
                    "vendor_type": vendor_type.value,
                },
            )
            return prompt_result

    # Fallback to local file
    return _load_local_prompt(vendor_type, schema_json)


def _load_local_prompt(vendor_type: VendorType, schema_json: str) -> "PromptResult":
    """Load prompt from local file.

    Args:
        vendor_type: Vendor type for template selection
        schema_json: JSON schema to inject into template

    Returns:
        PromptResult with local prompt content
    """
    from shared.adapters.observability import PromptResult

    vendor_file = PROMPTS_DIR / f"{vendor_type.value}.txt"

    if vendor_file.exists():
        template = vendor_file.read_text()
        logger.debug(f"Loaded local prompt template: {vendor_file.name}")
    else:
        generic_file = PROMPTS_DIR / "generic.txt"
        template = generic_file.read_text()
        logger.info(
            f"No template for {vendor_type.value}, using generic",
            extra={"vendor_type": vendor_type.value},
        )

    content = template.replace("{schema}", schema_json)

    return PromptResult(
        content=content,
        name=f"local-{vendor_type.value}",
        version=None,
        is_fallback=True,
    )


def load_prompt_template(vendor_type: VendorType) -> str:
    """Load vendor-specific prompt template (legacy function).

    Falls back to generic template if vendor-specific not found.
    Consider using load_prompt_with_langfuse() for LangFuse support.

    Args:
        vendor_type: Vendor type for template selection

    Returns:
        Prompt template with schema injected
    """
    schema = ExtractedInvoice.model_json_schema()
    result = _load_local_prompt(vendor_type, json.dumps(schema, indent=2))
    return result.content


def get_available_prompts() -> list[str]:
    """List available prompt templates.

    Returns:
        List of vendor types with available prompts
    """
    return [f.stem for f in PROMPTS_DIR.glob("*.txt")]


def calculate_extraction_scores(invoice: ExtractedInvoice) -> dict[str, float]:
    """Calculate quality scores for an extracted invoice.

    Scores:
    - validation_success: 1.0 (always 1 if we get here, validation passed)
    - field_completeness: % of optional fields that have non-default values
    - line_items_quality: Quality based on line item count and totals matching

    Args:
        invoice: Successfully validated ExtractedInvoice

    Returns:
        Dict of score_name -> score_value (0.0-1.0)
    """
    scores: dict[str, float] = {
        "validation_success": 1.0,  # If we're here, Pydantic validation passed
    }

    # Field completeness - check how many optional fields have values
    optional_fields_with_values = 0
    total_optional_fields = 5  # tax_amount, commission_rate, commission_amount, line_items, currency

    if invoice.tax_amount > 0:
        optional_fields_with_values += 1
    if invoice.commission_rate > 0:
        optional_fields_with_values += 1
    if invoice.commission_amount > 0:
        optional_fields_with_values += 1
    if invoice.line_items:
        optional_fields_with_values += 1
    if invoice.currency != "USD":  # Non-default currency specified
        optional_fields_with_values += 1

    scores["field_completeness"] = optional_fields_with_values / total_optional_fields

    # Line items quality - check if they sum approximately to subtotal
    if invoice.line_items:
        items_total = sum(item.amount for item in invoice.line_items)
        if invoice.subtotal > 0:
            match_ratio = min(float(items_total / invoice.subtotal), 1.0)
            scores["line_items_quality"] = abs(match_ratio - 1.0) < 0.1 and 1.0 or max(0.5, 1.0 - abs(match_ratio - 1.0))
        else:
            scores["line_items_quality"] = 0.5  # Can't verify without subtotal
    else:
        scores["line_items_quality"] = 0.0  # No line items

    return scores


def get_score_comments(invoice: ExtractedInvoice, scores: dict[str, float]) -> dict[str, str]:
    """Generate explanatory comments for each score.

    Args:
        invoice: The extracted invoice
        scores: Calculated scores

    Returns:
        Dict of score_name -> comment
    """
    comments: dict[str, str] = {
        "validation_success": "Pydantic schema validation passed",
    }

    # Field completeness comment
    fields_populated = []
    if invoice.tax_amount > 0:
        fields_populated.append("tax")
    if invoice.commission_rate > 0:
        fields_populated.append("commission_rate")
    if invoice.commission_amount > 0:
        fields_populated.append("commission_amount")
    if invoice.line_items:
        fields_populated.append(f"{len(invoice.line_items)} line_items")

    if fields_populated:
        comments["field_completeness"] = f"Fields populated: {', '.join(fields_populated)}"
    else:
        comments["field_completeness"] = "Only required fields populated"

    # Line items quality comment
    if invoice.line_items:
        items_total = sum(item.amount for item in invoice.line_items)
        diff = abs(float(items_total - invoice.subtotal))
        if diff < 0.10:
            comments["line_items_quality"] = f"Line items total matches subtotal (diff: ${diff:.2f})"
        else:
            comments["line_items_quality"] = f"Line items total differs from subtotal by ${diff:.2f}"
    else:
        comments["line_items_quality"] = "No line items extracted"

    return comments
