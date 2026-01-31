"""LLM adapter with Protocol interface and Gemini/OpenRouter implementations.

Provides:
- Protocol interface for testability
- Gemini 2.5 Flash via Vertex AI (primary)
- OpenRouter fallback (Claude 3.5 Sonnet)
- Retry logic with exponential backoff
- Optional LangFuse observability
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from shared.adapters.observability import LangfuseObserver


@dataclass
class LLMResponse:
    """Response from LLM API call."""

    success: bool
    content: str | None
    provider: Literal["gemini", "openrouter"]
    latency_ms: int
    tokens_used: int | None = None
    error_message: str | None = None


class LLMAdapter(Protocol):
    """Protocol for LLM extraction operations."""

    def extract(self, prompt: str, image_data: list[bytes]) -> LLMResponse:
        """Extract structured data from images using LLM.

        Args:
            prompt: Extraction prompt with JSON schema
            image_data: List of image bytes (PNG)

        Returns:
            LLMResponse with extraction result or error
        """
        ...


class GeminiAdapter:
    """Gemini 2.5 Flash via Vertex AI with optional LangFuse observability."""

    def __init__(
        self,
        project_id: str | None = None,
        region: str = "us-central1",
        model: str = "gemini-2.5-flash",
        max_retries: int = 2,
        timeout: int = 60,
        observer: LangfuseObserver | None = None,
    ):
        """Initialize Gemini adapter.

        Args:
            project_id: GCP project ID
            region: Vertex AI region
            model: Model name
            max_retries: Max retry attempts
            timeout: Request timeout in seconds
            observer: Optional LangFuse observer for tracing
        """
        self._project_id = project_id
        self._region = region
        self._model = model
        self._max_retries = max_retries
        self._timeout = timeout
        self._client = None
        self._observer = observer

    def _get_client(self):
        """Lazy-load Vertex AI client."""
        if self._client is None:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            vertexai.init(project=self._project_id, location=self._region)
            self._client = GenerativeModel(self._model)
        return self._client

    def extract(self, prompt: str, image_data: list[bytes]) -> LLMResponse:
        """Extract structured data using Gemini 2.5 Flash.

        Args:
            prompt: Extraction prompt
            image_data: List of PNG image bytes

        Returns:
            LLMResponse with extraction result
        """
        from vertexai.generative_models import Part

        start_time = time.time()
        retry_count = 0
        last_error = None
        generation_ctx = None

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

                contents = []
                for img_bytes in image_data:
                    image_part = Part.from_data(data=img_bytes, mime_type="image/png")
                    contents.append(image_part)

                contents.append(prompt)

                response = model.generate_content(
                    contents,
                    generation_config={
                        "temperature": 0.1,
                        "max_output_tokens": 4096,
                    },
                )

                latency_ms = int((time.time() - start_time) * 1000)

                if response.text:
                    input_tokens = getattr(
                        response.usage_metadata, "prompt_token_count", None
                    )
                    output_tokens = getattr(
                        response.usage_metadata, "candidates_token_count", None
                    )
                    total_tokens = None
                    if input_tokens is not None and output_tokens is not None:
                        total_tokens = input_tokens + output_tokens

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
                        tokens_used=total_tokens,
                    )
                else:
                    raise ValueError("Empty response from Gemini")

            except Exception as e:
                last_error = str(e)
                retry_count += 1

                if retry_count <= self._max_retries:
                    wait_time = 2 ** (retry_count - 1)
                    time.sleep(wait_time)

        latency_ms = int((time.time() - start_time) * 1000)

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


class OpenRouterAdapter:
    """OpenRouter fallback (Claude 3.5 Sonnet) with optional LangFuse observability."""

    def __init__(
        self,
        api_key: str,
        model: str = "anthropic/claude-3.5-sonnet",
        max_retries: int = 2,
        timeout: int = 60,
        observer: LangfuseObserver | None = None,
    ):
        """Initialize OpenRouter adapter.

        Args:
            api_key: OpenRouter API key
            model: Model name
            max_retries: Max retry attempts
            timeout: Request timeout in seconds
            observer: Optional LangFuse observer for tracing
        """
        self._api_key = api_key
        self._model = model
        self._max_retries = max_retries
        self._timeout = timeout
        self._observer = observer

    def extract(self, prompt: str, image_data: list[bytes]) -> LLMResponse:
        """Extract structured data using OpenRouter (Claude).

        Args:
            prompt: Extraction prompt
            image_data: List of PNG image bytes

        Returns:
            LLMResponse with extraction result
        """
        from openai import OpenAI

        start_time = time.time()
        retry_count = 0
        last_error = None
        generation_ctx = None

        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=self._api_key)

        if self._observer:
            generation_ctx = self._observer.start_generation(
                name="openrouter-extraction",
                model=self._model,
                prompt=prompt,
                model_parameters={"temperature": 0.1, "max_tokens": 4096},
                metadata={
                    "provider": "openrouter",
                    "retry_attempt": retry_count,
                    "image_count": len(image_data),
                },
            )

        while retry_count <= self._max_retries:
            try:
                content_parts = []

                for img_bytes in image_data:
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                    content_parts.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                        }
                    )

                content_parts.append({"type": "text", "text": prompt})

                response = client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": content_parts}],
                    temperature=0.1,
                    max_tokens=4096,
                    timeout=self._timeout,
                )

                latency_ms = int((time.time() - start_time) * 1000)

                if response.choices and response.choices[0].message.content:
                    input_tokens = None
                    output_tokens = None
                    total_tokens = None

                    if response.usage:
                        input_tokens = response.usage.prompt_tokens
                        output_tokens = response.usage.completion_tokens
                        total_tokens = response.usage.total_tokens

                    if self._observer:
                        self._observer.end_generation(
                            ctx=generation_ctx,
                            output=response.choices[0].message.content,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            success=True,
                        )

                    return LLMResponse(
                        success=True,
                        content=response.choices[0].message.content,
                        provider="openrouter",
                        latency_ms=latency_ms,
                        tokens_used=total_tokens,
                    )
                else:
                    raise ValueError("Empty response from OpenRouter")

            except Exception as e:
                last_error = str(e)
                retry_count += 1

                if retry_count <= self._max_retries:
                    wait_time = 2 ** (retry_count - 1)
                    time.sleep(wait_time)

        latency_ms = int((time.time() - start_time) * 1000)

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
            provider="openrouter",
            latency_ms=latency_ms,
            error_message=f"OpenRouter failed after {self._max_retries} retries: {last_error}",
        )
