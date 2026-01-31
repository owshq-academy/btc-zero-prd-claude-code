# DESIGN: LangFuse Observability for Invoice Extraction

> Technical design for instrumenting LLM calls with LangFuse in the data_extractor function

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | LANGFUSE_OBSERVABILITY |
| **Date** | 2026-01-30 |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_LANGFUSE_OBSERVABILITY.md](./DEFINE_LANGFUSE_OBSERVABILITY.md) |
| **Status** | Ready for Build |

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                     LANGFUSE OBSERVABILITY ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐                                                        │
│  │  data_extractor │                                                        │
│  │     (main.py)   │                                                        │
│  └────────┬────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                    extractor.py                              │            │
│  │  extract_invoice() → _try_extraction() → adapter.extract()  │            │
│  └─────────────────────────────────────┬───────────────────────┘            │
│                                        │                                     │
│                                        ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                  LLM ADAPTERS (llm.py)                       │            │
│  │  ┌───────────────────┐     ┌────────────────────┐           │            │
│  │  │   GeminiAdapter   │     │  OpenRouterAdapter │           │            │
│  │  │  ┌─────────────┐  │     │  ┌─────────────┐   │           │            │
│  │  │  │  observer   │──┼─────┼──│  observer   │   │           │            │
│  │  │  └─────────────┘  │     │  └─────────────┘   │           │            │
│  │  └───────────────────┘     └────────────────────┘           │            │
│  └─────────────────────────────────┬───────────────────────────┘            │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │              LangfuseObserver (observability.py)             │            │
│  │  ┌─────────────────────────────────────────────────────┐    │            │
│  │  │  start_generation()  → LangFuse generation span     │    │            │
│  │  │  end_generation()    → Update with response, tokens │    │            │
│  │  │  score_extraction()  → Add confidence score         │    │            │
│  │  │  flush()             → Send to LangFuse cloud       │    │            │
│  │  └─────────────────────────────────────────────────────┘    │            │
│  │                           │                                  │            │
│  │                           │ try/catch (silent fallback)      │            │
│  │                           ▼                                  │            │
│  │  ┌─────────────────────────────────────────────────────┐    │            │
│  │  │  Langfuse SDK (langfuse.get_client())               │    │            │
│  │  └─────────────────────────────────────────────────────┘    │            │
│  └─────────────────────────────────────┬───────────────────────┘            │
│                                        │                                     │
│                                        ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                     LangFuse Cloud                           │            │
│  │  • Traces & Generations                                      │            │
│  │  • Token Usage & Cost                                        │            │
│  │  • Latency Metrics                                           │            │
│  │  • Confidence Scores                                         │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **LangfuseObserver** | Encapsulates all LangFuse SDK calls with error handling | Python, langfuse SDK |
| **GeminiAdapter** | Gemini 2.5 Flash via Vertex AI (modified to accept observer) | vertexai, langfuse |
| **OpenRouterAdapter** | Claude 3.5 Sonnet fallback (modified to accept observer) | openai SDK, langfuse |
| **Config** | Extended with LangFuse environment variables | dataclass, lru_cache |

---

## Key Decisions

### Decision 1: Observer Pattern for LangFuse Instrumentation

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** We need to add LangFuse tracing to LLM adapters without tightly coupling the adapter code to the LangFuse SDK.

**Choice:** Create a `LangfuseObserver` class that encapsulates all LangFuse SDK calls. Inject the observer into adapters via constructor parameter with `None` as default.

**Rationale:**
- **Testability**: Adapters can be tested without LangFuse by passing `None`
- **Single Responsibility**: Observer handles all observability logic
- **Silent Fallback**: Observer's try/catch prevents LangFuse failures from affecting extraction
- **Optional**: Existing code works unchanged if no observer is provided

**Alternatives Rejected:**
1. **Decorator pattern** - Rejected because it doesn't give access to internal retry state
2. **Middleware/hooks** - Rejected because adapters don't have a middleware system
3. **Modify SDK directly** - Rejected because it would couple adapters to LangFuse

**Consequences:**
- Adapters gain an optional `observer` parameter
- Observer must handle its own errors silently
- Slightly more complex adapter constructors

---

### Decision 2: Generation-Level Tracing (Not Trace + Span)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** LangFuse offers hierarchical tracing (Trace → Span → Generation). We need to decide the granularity.

**Choice:** Create a single `generation` observation per LLM call. No parent trace or child spans.

**Rationale:**
- **Simplicity**: Each extraction is independent, no need for hierarchy
- **Cost/Token Focus**: `generation` type is optimized for LLM metrics
- **Future Extensible**: Can add parent trace later for pipeline-level tracing

**Alternatives Rejected:**
1. **Full trace hierarchy** - Rejected because scope is extraction-only (not full pipeline)
2. **Span only** - Rejected because it lacks token/cost tracking features

**Consequences:**
- Each LLM call creates one generation in LangFuse
- No cross-function trace linking (deferred to future)
- Simpler implementation, faster time to value

---

### Decision 3: Confidence Scoring via Schema Validation Success

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** We need to attach confidence scores to extractions, but no ground truth dataset exists.

**Choice:** Score confidence as 1.0 for successful Pydantic validation, 0.0 for failure. Future: add partial scoring for validation warnings.

**Rationale:**
- **Available Now**: Schema validation is already happening
- **Binary Signal**: Valid/invalid is meaningful for quality tracking
- **Extensible**: Can enhance scoring logic without API changes

**Alternatives Rejected:**
1. **LLM-as-Judge** - Rejected because no ground truth for prompt design
2. **Skip scoring** - Rejected because it's a MUST requirement

**Consequences:**
- Initial scores are binary (0.0 or 1.0)
- Score name: `extraction_confidence`
- Can be enhanced post-MVP with more nuanced scoring

---

### Decision 4: Environment Variables via Secret Manager

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-01-30 |

**Context:** LangFuse requires `LANGFUSE_SECRET_KEY` and `LANGFUSE_PUBLIC_KEY` for authentication.

**Choice:**
- `LANGFUSE_PUBLIC_KEY`: Set as Cloud Run environment variable
- `LANGFUSE_SECRET_KEY`: Mounted from GCP Secret Manager

**Rationale:**
- **Security**: Secret key not in plaintext environment
- **IaC Compatible**: Terraform can manage secret mounting
- **Existing Pattern**: Matches how `OPENROUTER_API_KEY` is handled

**Alternatives Rejected:**
1. **Both as env vars** - Rejected because secret key should be in Secret Manager
2. **Hardcoded in code** - Rejected for obvious security reasons

**Consequences:**
- Terraform changes required to create secret and mount it
- `get_config()` extended with LangFuse fields

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `functions/gcp/v1/src/shared/adapters/observability.py` | Create | LangfuseObserver class with all SDK calls | @python-developer | None |
| 2 | `functions/gcp/v1/src/shared/adapters/llm.py` | Modify | Add observer parameter to adapters | @function-developer | 1 |
| 3 | `functions/gcp/v1/src/shared/utils/config.py` | Modify | Add LangFuse configuration fields | @python-developer | None |
| 4 | `functions/gcp/v1/tests/unit/test_observability.py` | Create | Unit tests for LangfuseObserver | @test-generator | 1 |
| 5 | `functions/gcp/v1/tests/unit/test_llm.py` | Modify | Update tests for observer injection | @test-generator | 2, 4 |

**Total Files:** 5 (2 create, 3 modify)

---

## Agent Assignment Rationale

| Agent | Files Assigned | Why This Agent |
|-------|----------------|----------------|
| @python-developer | 1, 3 | Clean Python patterns: dataclasses, type hints, error handling |
| @function-developer | 2 | Cloud Run function context, GCP patterns |
| @test-generator | 4, 5 | pytest fixtures, mocking LangFuse SDK |

**Agent Discovery:**
- Scanned: `.claude/agents/**/*.md`
- Matched by: File type (Python), purpose (observability, testing), KB domains (langfuse)

---

## Code Patterns

### Pattern 1: LangfuseObserver Class

```python
"""
LangFuse observer for LLM call instrumentation.
Handles all SDK calls with silent fallback on errors.
"""
from dataclasses import dataclass
from typing import Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class GenerationContext:
    """Context for an active LangFuse generation."""
    generation: Any  # LangFuse observation object
    trace_id: str
    start_time: float


class LangfuseObserver:
    """Observer for LLM call tracing with LangFuse.

    All methods are safe to call - errors are logged but never raised.
    This ensures LangFuse issues never block invoice processing.
    """

    def __init__(self, enabled: bool = True):
        """Initialize observer.

        Args:
            enabled: If False, all methods are no-ops (for testing)
        """
        self._enabled = enabled
        self._client = None
        self._current_generation: GenerationContext | None = None

    def _get_client(self):
        """Lazy-load LangFuse client with error handling."""
        if not self._enabled:
            return None
        if self._client is None:
            try:
                from langfuse import get_client
                self._client = get_client()
                if not self._client.auth_check():
                    logger.warning("LangFuse auth check failed")
                    self._client = None
            except Exception as e:
                logger.warning(f"LangFuse initialization failed: {e}")
                self._client = None
        return self._client

    def start_generation(
        self,
        name: str,
        model: str,
        prompt: str,
        model_parameters: dict,
        metadata: dict,
    ) -> GenerationContext | None:
        """Start a new LangFuse generation observation.

        Args:
            name: Generation name (e.g., "gemini-extraction")
            model: Model identifier
            prompt: Full prompt text
            model_parameters: {temperature, max_tokens}
            metadata: {provider, retry_attempt, image_count}

        Returns:
            GenerationContext if successful, None otherwise
        """
        try:
            import time
            client = self._get_client()
            if client is None:
                return None

            generation = client.start_as_current_observation(
                as_type="generation",
                name=name,
                model=model,
                model_parameters=model_parameters,
                input=prompt,
                metadata=metadata,
            )

            ctx = GenerationContext(
                generation=generation.__enter__(),
                trace_id=generation.trace_id,
                start_time=time.time(),
            )
            self._current_generation = ctx
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
        """End a LangFuse generation and record output.

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
            usage_details = {}
            if input_tokens is not None:
                usage_details["input"] = input_tokens
            if output_tokens is not None:
                usage_details["output"] = output_tokens

            ctx.generation.update(
                output=output or error_message,
                usage_details=usage_details if usage_details else None,
            )

            # Exit context manager
            ctx.generation.__exit__(None, None, None)
            self._current_generation = None

        except Exception as e:
            logger.warning(f"LangFuse end_generation failed: {e}")

    def score_extraction(
        self,
        ctx: GenerationContext | None,
        confidence: float,
        comment: str | None = None,
    ) -> None:
        """Score the extraction quality.

        Args:
            ctx: Generation context
            confidence: Confidence score 0.0-1.0
            comment: Optional comment
        """
        if ctx is None:
            return

        try:
            ctx.generation.score(
                name="extraction_confidence",
                value=confidence,
                data_type="NUMERIC",
                comment=comment,
            )
        except Exception as e:
            logger.warning(f"LangFuse score_extraction failed: {e}")

    def flush(self) -> None:
        """Flush pending events to LangFuse. Call before process exit."""
        try:
            client = self._get_client()
            if client:
                client.flush()
        except Exception as e:
            logger.warning(f"LangFuse flush failed: {e}")
```

### Pattern 2: Modified GeminiAdapter with Observer

```python
class GeminiAdapter:
    """Gemini 2.5 Flash via Vertex AI with optional LangFuse observability."""

    def __init__(
        self,
        project_id: str | None = None,
        region: str = "us-central1",
        model: str = "gemini-2.5-flash",
        max_retries: int = 2,
        timeout: int = 60,
        observer: LangfuseObserver | None = None,  # NEW
    ):
        self._project_id = project_id
        self._region = region
        self._model = model
        self._max_retries = max_retries
        self._timeout = timeout
        self._client = None
        self._observer = observer  # NEW

    def extract(self, prompt: str, image_data: list[bytes]) -> LLMResponse:
        """Extract structured data using Gemini 2.5 Flash."""
        from vertexai.generative_models import Part

        start_time = time.time()
        retry_count = 0
        last_error = None
        generation_ctx = None

        # Start LangFuse generation
        if self._observer:
            generation_ctx = self._observer.start_generation(
                name="gemini-extraction",
                model=self._model,
                prompt=prompt,
                model_parameters={"temperature": 0.1, "max_output_tokens": 4096},
                metadata={
                    "provider": "gemini",
                    "retry_attempt": retry_count,
                    "image_count": len(image_data),
                },
            )

        while retry_count <= self._max_retries:
            try:
                model = self._get_client()
                contents = [Part.from_data(data=img, mime_type="image/png") for img in image_data]
                contents.append(prompt)

                response = model.generate_content(
                    contents,
                    generation_config={"temperature": 0.1, "max_output_tokens": 4096},
                )

                latency_ms = int((time.time() - start_time) * 1000)

                if response.text:
                    # Extract token usage from Gemini response
                    input_tokens = getattr(response.usage_metadata, 'prompt_token_count', None)
                    output_tokens = getattr(response.usage_metadata, 'candidates_token_count', None)

                    # End LangFuse generation
                    if self._observer:
                        self._observer.end_generation(
                            ctx=generation_ctx,
                            output=response.text,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            success=True,
                        )

                    return LLMResponse(
                        success=True,
                        content=response.text,
                        provider="gemini",
                        latency_ms=latency_ms,
                        tokens_used=input_tokens + output_tokens if input_tokens and output_tokens else None,
                    )
                else:
                    raise ValueError("Empty response from Gemini")

            except Exception as e:
                last_error = str(e)
                retry_count += 1
                if retry_count <= self._max_retries:
                    time.sleep(2 ** (retry_count - 1))

        latency_ms = int((time.time() - start_time) * 1000)

        # End LangFuse generation with error
        if self._observer:
            self._observer.end_generation(
                ctx=generation_ctx,
                output=None,
                input_tokens=None,
                output_tokens=None,
                success=False,
                error_message=last_error,
            )

        return LLMResponse(
            success=False,
            content=None,
            provider="gemini",
            latency_ms=latency_ms,
            error_message=f"Gemini failed after {self._max_retries} retries: {last_error}",
        )
```

### Pattern 3: Extended Config

```python
@dataclass(frozen=True)
class Config:
    """Application configuration from environment variables."""

    # ... existing fields ...

    # LangFuse configuration (NEW)
    langfuse_public_key: str | None
    langfuse_secret_key: str | None
    langfuse_base_url: str
    langfuse_enabled: bool


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Load configuration from environment (cached)."""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "invoice-pipeline-dev")

    # Determine if LangFuse should be enabled
    langfuse_public = os.environ.get("LANGFUSE_PUBLIC_KEY")
    langfuse_secret = os.environ.get("LANGFUSE_SECRET_KEY")
    langfuse_enabled = bool(langfuse_public and langfuse_secret)

    return Config(
        # ... existing fields ...

        # LangFuse (NEW)
        langfuse_public_key=langfuse_public,
        langfuse_secret_key=langfuse_secret,
        langfuse_base_url=os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
        langfuse_enabled=langfuse_enabled,
    )
```

---

## Data Flow

```text
1. extract_invoice() called with images and vendor type
   │
   ▼
2. GeminiAdapter.extract() invoked
   │
   ├──► observer.start_generation() → LangFuse generation created
   │
   ▼
3. Gemini API called (with retries)
   │
   ├──► Success: observer.end_generation(output, tokens)
   │              observer.score_extraction(confidence=1.0)
   │
   └──► Failure after retries: observer.end_generation(error=msg)
                                Try OpenRouterAdapter (same flow)
   │
   ▼
4. LLMResponse returned to extractor.py
   │
   ▼
5. observer.flush() called before Cloud Run exits
   │
   ▼
6. Traces visible in LangFuse dashboard
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|-----------------|----------------|
| **LangFuse Cloud** | REST API via SDK | LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY |
| **Vertex AI** | gRPC via SDK | Service Account (existing) |
| **OpenRouter** | REST via OpenAI SDK | OPENROUTER_API_KEY (existing) |
| **GCP Secret Manager** | Mounted secret | Terraform-managed |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|---------------|
| Unit | LangfuseObserver methods | `test_observability.py` | pytest, unittest.mock | 90% |
| Unit | Adapter with observer | `test_llm.py` | pytest, MagicMock | 80% |
| Integration | End-to-end with mock | `test_pipeline.py` | pytest, responses | Key paths |
| Manual | LangFuse dashboard | N/A | Browser | Verify traces appear |

### Key Test Scenarios

| Test | Description |
|------|-------------|
| `test_observer_disabled` | Observer does nothing when enabled=False |
| `test_observer_silent_fallback` | SDK errors logged but not raised |
| `test_gemini_with_observer` | Tokens and latency traced correctly |
| `test_fallback_both_traced` | Both Gemini and OpenRouter attempts visible |
| `test_confidence_scoring` | Score attached to generation |

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|-------------------|--------|
| LangFuse SDK import fails | Log warning, disable observer | No |
| LangFuse auth check fails | Log warning, disable observer | No |
| start_generation fails | Log warning, return None | No |
| end_generation fails | Log warning, continue | No |
| flush fails | Log warning, continue | No |
| Gemini API error | Retry with backoff, then fallback | Yes |
| OpenRouter API error | Retry with backoff, then fail | Yes |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `LANGFUSE_PUBLIC_KEY` | string | None | LangFuse public API key |
| `LANGFUSE_SECRET_KEY` | string | None | LangFuse secret key (from Secret Manager) |
| `LANGFUSE_BASE_URL` | string | `https://cloud.langfuse.com` | LangFuse server endpoint |

---

## Security Considerations

- **Secret Key in Secret Manager**: Never in plaintext environment variables
- **No Image Logging**: Only image count, not actual image bytes
- **No PII in Traces**: Invoice data in responses may contain PII; LangFuse handles encryption
- **API Keys Scoped**: LangFuse keys are project-scoped, not org-wide

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| **Logging** | Structured JSON via existing logger; LangFuse failures logged at WARNING |
| **Metrics** | LangFuse dashboard: tokens, cost, latency, scores |
| **Tracing** | LangFuse generations with full prompt/response capture |
| **Alerting** | Use LangFuse built-in cost/latency dashboards (defer custom alerts) |

---

## Acceptance Test Mapping

| AT ID | Design Element | How It's Addressed |
|-------|----------------|-------------------|
| AT-001 | GeminiAdapter + observer | `start_generation` + `end_generation` captures all data |
| AT-002 | Both adapters traced | Same observer pattern for OpenRouterAdapter |
| AT-003 | Cost in dashboard | `usage_details` with tokens enables auto-cost |
| AT-004 | Confidence = 1.0 | `score_extraction(confidence=1.0)` after validation |
| AT-005 | Confidence < 1.0 | Future: integrate with validation warnings |
| AT-006 | Silent fallback | All observer methods wrapped in try/catch |
| AT-007 | < 50ms overhead | SDK is async; measure in integration tests |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-30 | design-agent | Initial version |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_LANGFUSE_OBSERVABILITY.md`
