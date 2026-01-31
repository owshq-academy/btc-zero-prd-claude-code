"""LangFuse observer for LLM call instrumentation.

Provides:
- End-to-end distributed tracing across pipeline functions
- Session-based grouping for related invoices
- Generation-level tracing for LLM calls (required for cost tracking)
- Token usage and cost tracking via usage_details
- Confidence scoring for extractions
- Prompt Management integration with fallback
- Silent fallback on errors (never blocks invoice processing)

All methods are safe to call - errors are logged but never raised.

Updated for LangFuse SDK v2 API with distributed tracing support.

SDK v2 Key Methods:
- langfuse.start_span(name=...) - manual span management without context manager
- langfuse.start_as_current_observation(as_type="generation", trace_context={...}) - for generations
- span.update(output=..., usage_details={...}) - update with usage for cost tracking
- langfuse.create_score(trace_id=..., name=..., value=...) - create scores
- langfuse.flush() - ensure all data is sent

IMPORTANT: Cost tracking requires:
1. Using generation type (not span) - only generation/embedding support costs
2. Passing usage_details dict with 'input', 'output' keys
3. Model name must match LangFuse's model definitions (or add custom model)
"""

import logging
import os
import time
import uuid
from contextlib import nullcontext
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TraceContext:
    """Context for distributed tracing across pipeline functions.

    Passed via Pub/Sub messages to link spans across Cloud Run functions.

    Attributes:
        trace_id: W3C trace ID (32 hex chars) - shared across entire pipeline
        session_id: LangFuse session ID for grouping related invoices
        parent_span_id: W3C span ID (16 hex chars) of the parent span
    """

    trace_id: str
    session_id: str | None = None
    parent_span_id: str | None = None

    @classmethod
    def from_message(cls, message: Any) -> "TraceContext":
        """Create TraceContext from a Pub/Sub message with trace fields."""
        return cls(
            trace_id=getattr(message, "trace_id", uuid.uuid4().hex),
            session_id=getattr(message, "session_id", None),
            parent_span_id=getattr(message, "parent_span_id", None),
        )


@dataclass
class GenerationContext:
    """Context for an active LangFuse generation/span.

    Attributes:
        trace_id: Unique trace identifier (32 hex chars)
        span_id: This span's ID (16 hex chars)
        generation_id: Unique generation identifier
        start_time: Unix timestamp when generation started
        name: Generation name
        model: Model identifier
    """

    trace_id: str
    span_id: str
    generation_id: str
    start_time: float
    name: str
    model: str
    _span: Any = field(default=None, repr=False)


@dataclass
class PromptResult:
    """Result from fetching a prompt from LangFuse.

    Attributes:
        content: The compiled prompt text
        name: Prompt name in LangFuse
        version: Prompt version number
        is_fallback: True if using local fallback (LangFuse unavailable)
    """

    content: str
    name: str
    version: int | None = None
    is_fallback: bool = False


class LangfuseObserver:
    """Observer for LLM call tracing with LangFuse.

    Supports distributed tracing across pipeline functions using W3C trace context.
    All methods are safe to call - errors are logged but never raised.

    Example (distributed tracing):
        observer = LangfuseObserver()

        # From incoming Pub/Sub message
        trace_ctx = TraceContext.from_message(classified_message)

        # Start a span under the shared trace
        ctx = observer.start_generation(
            name="gemini-extraction",
            model="gemini-2.5-flash",
            prompt="Extract invoice...",
            model_parameters={"temperature": 0.1},
            metadata={"vendor_type": "grubhub"},
            trace_context=trace_ctx,  # Links to parent trace
        )

        # Make LLM call...
        observer.end_generation(ctx, output=response, input_tokens=100, output_tokens=50, success=True)
        observer.score_extraction(ctx, confidence=1.0)
        observer.flush()

    Example (prompt management):
        prompt_result = observer.get_prompt(
            name="extraction-grubhub",
            fallback_path=Path("prompts/grubhub.txt"),
            variables={"schema": json_schema},
        )
        # prompt_result.content contains the compiled prompt
        # prompt_result.version contains the LangFuse version (or None if fallback)
    """

    def __init__(self, enabled: bool = True):
        """Initialize observer.

        Args:
            enabled: If False, all methods are no-ops (for testing)
        """
        self._enabled = enabled
        self._client: Any = None
        self._prompt_cache: dict[str, Any] = {}

    def _get_client(self) -> Any:
        """Lazy-load LangFuse client with error handling.

        Returns:
            LangFuse client or None if initialization fails
        """
        if not self._enabled:
            return None

        if self._client is None:
            try:
                from langfuse import Langfuse

                self._client = Langfuse()
                if not self._client.auth_check():
                    logger.warning("LangFuse auth check failed - disabling observability")
                    self._client = None
            except ImportError:
                logger.warning("LangFuse SDK not installed - disabling observability")
                self._client = None
            except Exception as e:
                logger.warning(f"LangFuse initialization failed: {e}")
                self._client = None

        return self._client

    def get_prompt(
        self,
        name: str,
        fallback_path: Path | None = None,
        variables: dict[str, Any] | None = None,
        label: str = "production",
    ) -> PromptResult:
        """Fetch a versioned prompt from LangFuse Prompt Management.

        Falls back to local file if LangFuse is unavailable or prompt not found.

        Args:
            name: Prompt name in LangFuse (e.g., "extraction-grubhub")
            fallback_path: Path to local prompt file for fallback
            variables: Variables to compile into the prompt template
            label: LangFuse prompt label (default: "production")

        Returns:
            PromptResult with compiled prompt content and version info
        """
        variables = variables or {}

        try:
            client = self._get_client()
            if client is not None:
                # Fetch from LangFuse with caching
                cache_key = f"{name}:{label}"
                if cache_key not in self._prompt_cache:
                    self._prompt_cache[cache_key] = client.get_prompt(name, label=label)

                langfuse_prompt = self._prompt_cache[cache_key]
                compiled = langfuse_prompt.compile(**variables)

                logger.info(
                    f"Loaded prompt from LangFuse: {name} v{langfuse_prompt.version}"
                )

                return PromptResult(
                    content=compiled,
                    name=name,
                    version=langfuse_prompt.version,
                    is_fallback=False,
                )

        except Exception as e:
            logger.warning(f"LangFuse prompt fetch failed for '{name}': {e}")

        # Fallback to local file
        if fallback_path and fallback_path.exists():
            content = fallback_path.read_text()
            # Simple variable substitution for local files
            for key, value in variables.items():
                content = content.replace(f"{{{key}}}", str(value))

            logger.info(f"Using local fallback prompt: {fallback_path}")

            return PromptResult(
                content=content,
                name=name,
                version=None,
                is_fallback=True,
            )

        # No prompt available
        logger.error(f"No prompt available for '{name}' - no fallback path provided")
        return PromptResult(
            content="",
            name=name,
            version=None,
            is_fallback=True,
        )

    def start_generation(
        self,
        name: str,
        model: str,
        prompt: str,
        model_parameters: dict[str, Any],
        metadata: dict[str, Any],
        trace_context: TraceContext | None = None,
        prompt_info: PromptResult | None = None,
    ) -> GenerationContext | None:
        """Start a new LangFuse generation observation with distributed tracing.

        Uses LangFuse SDK v2 API:
        - start_as_current_observation(as_type="generation") for generation with cost tracking
        - trace_context parameter for distributed tracing with custom trace_id
        - Manual context manager handling for non-context-manager usage pattern

        Args:
            name: Generation name (e.g., "gemini-extraction")
            model: Model identifier (e.g., "gemini-2.5-flash")
            prompt: Full prompt text
            model_parameters: Dict with temperature, max_tokens, etc.
            metadata: Additional metadata (provider, retry_attempt, image_count)
            trace_context: Optional trace context for distributed tracing
            prompt_info: Optional prompt info to link to LangFuse prompt

        Returns:
            GenerationContext if successful, None otherwise
        """
        try:
            client = self._get_client()
            if client is None:
                return None

            # Combine metadata with model info
            full_metadata = {
                **metadata,
                "model": model,
                "model_parameters": model_parameters,
            }

            # Add prompt info to metadata if available
            if prompt_info and not prompt_info.is_fallback:
                full_metadata["prompt_name"] = prompt_info.name
                full_metadata["prompt_version"] = prompt_info.version

            # Generate span ID for this generation
            span_id = uuid.uuid4().hex[:16]

            # Determine trace_id and session_id from context
            trace_id = trace_context.trace_id if trace_context else uuid.uuid4().hex
            session_id = trace_context.session_id if trace_context else None
            parent_span_id = trace_context.parent_span_id if trace_context else None

            # SDK v2 Pattern: Use start_as_current_observation with as_type="generation"
            # This creates a generation observation that supports cost tracking
            # We manually enter the context manager and store it for later exit
            #
            # Build trace_context dict for distributed tracing
            lf_trace_context = {"trace_id": trace_id}
            if parent_span_id:
                lf_trace_context["parent_span_id"] = parent_span_id

            # Add session_id to metadata since it's not a direct parameter
            if session_id:
                full_metadata["session_id"] = session_id

            # Create the context manager for the generation
            ctx_mgr = client.start_as_current_observation(
                as_type="generation",
                name=name,
                model=model,
                model_parameters=model_parameters,
                input={"prompt": prompt[:1000], "prompt_length": len(prompt)},
                metadata=full_metadata,
                trace_context=lf_trace_context,
            )

            # Manually enter the context manager
            generation = ctx_mgr.__enter__()

            ctx = GenerationContext(
                trace_id=trace_id,
                span_id=span_id,
                generation_id=getattr(generation, 'id', str(uuid.uuid4())),
                start_time=time.time(),
                name=name,
                model=model,
                _span=(ctx_mgr, generation),  # Store both context manager and generation
            )
            return ctx

        except Exception as e:
            logger.warning(f"LangFuse start_generation failed: {e}")
            return None

    def end_generation(
        self,
        ctx: GenerationContext | None,
        output: str | None,
        input_tokens: int | None,
        output_tokens: int | None,
        success: bool,
        error_message: str | None = None,
    ) -> None:
        """End a LangFuse generation and record output with usage for cost tracking.

        SDK v2 Pattern:
        1. generation.update() with output and usage_details for cost tracking
        2. Exit context manager to complete the observation

        Args:
            ctx: Generation context from start_generation
            output: LLM response text
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            success: Whether extraction succeeded
            error_message: Error message if failed
        """
        if ctx is None:
            return

        try:
            # Build output data
            output_data: dict[str, Any] = {
                "success": success,
                "output_preview": (output or error_message or "")[:500],
            }

            # Build usage_details dict for cost tracking (SDK v2)
            # Keys: 'input', 'output', 'total' (tokens)
            # LangFuse calculates cost based on model pricing configuration
            usage_details: dict[str, int] | None = None
            if input_tokens is not None or output_tokens is not None:
                usage_details = {}
                if input_tokens is not None:
                    usage_details["input"] = input_tokens
                if output_tokens is not None:
                    usage_details["output"] = output_tokens
                if input_tokens and output_tokens:
                    usage_details["total"] = input_tokens + output_tokens

            # ctx._span is a tuple: (context_manager, generation_object)
            if ctx._span:
                ctx_mgr, generation = ctx._span

                # Update the generation with output and usage_details for cost tracking
                update_kwargs: dict[str, Any] = {
                    "output": output_data,
                    "level": "ERROR" if not success else "DEFAULT",
                }

                if error_message and not success:
                    update_kwargs["status_message"] = error_message

                # Add usage_details for cost tracking
                if usage_details:
                    update_kwargs["usage_details"] = usage_details

                # Update the generation
                generation.update(**update_kwargs)

                # Exit the context manager to complete the observation
                ctx_mgr.__exit__(None, None, None)

        except Exception as e:
            logger.warning(f"LangFuse end_generation failed: {e}")

    def score_extraction(
        self,
        ctx: GenerationContext | None,
        confidence: float,
        comment: str | None = None,
    ) -> None:
        """Score the extraction quality on the generation.

        SDK v2 Pattern: Use generation.score() to attach score to the observation.
        Note: Must be called BEFORE end_generation() to attach score to span.

        Args:
            ctx: Generation context
            confidence: Confidence score 0.0-1.0
            comment: Optional comment explaining the score
        """
        if ctx is None:
            return

        try:
            # ctx._span is a tuple: (context_manager, generation_object)
            if ctx._span:
                _, generation = ctx._span
                generation.score(
                    name="extraction_confidence",
                    value=confidence,
                    data_type="NUMERIC",
                    comment=comment,
                )

        except Exception as e:
            logger.warning(f"LangFuse score_extraction failed: {e}")

    def score_trace(
        self,
        trace_id: str,
        scores: dict[str, float | int | bool],
        comments: dict[str, str] | None = None,
    ) -> None:
        """Add multiple scores to a trace after processing completes.

        SDK v2 Pattern: Use client.create_score() to add scores to traces.
        Scores are visible in the LangFuse dashboard under the trace.

        Args:
            trace_id: The trace ID to score
            scores: Dict of score_name -> score_value (0.0-1.0 for float, 0/1 for bool)
            comments: Optional dict of score_name -> comment

        Example:
            observer.score_trace(
                trace_id="abc123...",
                scores={
                    "extraction_confidence": 0.95,
                    "validation_success": 1,
                    "field_completeness": 0.85,
                },
                comments={
                    "extraction_confidence": "All fields extracted successfully",
                    "field_completeness": "9 of 11 optional fields populated",
                }
            )
        """
        comments = comments or {}

        try:
            client = self._get_client()
            if client is None:
                return

            for score_name, score_value in scores.items():
                # Determine data type and value based on input type
                if isinstance(score_value, bool):
                    numeric_value = 1 if score_value else 0
                    data_type = "NUMERIC"
                elif isinstance(score_value, int):
                    numeric_value = float(score_value)
                    data_type = "NUMERIC"
                else:
                    numeric_value = float(score_value)
                    data_type = "NUMERIC"

                # SDK v2: Use create_score() instead of score()
                client.create_score(
                    trace_id=trace_id,
                    name=score_name,
                    value=numeric_value,
                    data_type=data_type,
                    comment=comments.get(score_name),
                )

            logger.debug(
                f"Scored trace {trace_id[:16]}... with {len(scores)} scores"
            )

        except Exception as e:
            logger.warning(f"LangFuse score_trace failed: {e}")

    def get_span_id(self, ctx: GenerationContext | None) -> str | None:
        """Get the span ID from a generation context.

        Use this to pass to the next function in the pipeline as parent_span_id.

        Args:
            ctx: Generation context

        Returns:
            Span ID string or None
        """
        if ctx is None:
            return None
        return ctx.span_id

    def flush(self) -> None:
        """Flush pending events to LangFuse.

        Call before process exit to ensure all traces are sent.
        Critical for Cloud Run functions that may terminate quickly.
        """
        try:
            client = self._get_client()
            if client:
                client.flush()
        except Exception as e:
            logger.warning(f"LangFuse flush failed: {e}")

    @property
    def is_enabled(self) -> bool:
        """Check if observer is enabled and client is available."""
        return self._enabled and self._get_client() is not None


def create_observer(enabled: bool | None = None) -> LangfuseObserver:
    """Factory function to create a LangfuseObserver.

    Args:
        enabled: Override enabled state. If None, checks for LangFuse env vars.

    Returns:
        Configured LangfuseObserver instance
    """
    if enabled is None:
        public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
        secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
        enabled = bool(public_key and secret_key)

    return LangfuseObserver(enabled=enabled)
