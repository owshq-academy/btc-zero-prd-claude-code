"""Unit tests for LangFuse observability module.

Tests cover:
- Observer initialization
- Silent fallback on errors
- Generation lifecycle (start, end, score)
- Disabled observer behavior
- Distributed tracing with TraceContext
- Prompt Management integration

Updated for LangFuse SDK v2 API with distributed tracing support.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from shared.adapters.observability import (
    GenerationContext,
    LangfuseObserver,
    PromptResult,
    TraceContext,
    create_observer,
)


class TestLangfuseObserver:
    """Tests for LangfuseObserver class."""

    def test_observer_disabled_returns_none(self):
        """Observer with enabled=False should return None for all operations."""
        observer = LangfuseObserver(enabled=False)

        ctx = observer.start_generation(
            name="test",
            model="gemini-2.5-flash",
            prompt="Test prompt",
            model_parameters={"temperature": 0.1},
            metadata={"provider": "gemini"},
        )

        assert ctx is None
        assert observer.is_enabled is False

    def test_observer_enabled_but_no_sdk(self):
        """Observer with enabled=True but missing SDK should handle gracefully."""
        observer = LangfuseObserver(enabled=True)

        with patch.dict(sys.modules, {"langfuse": None}):
            ctx = observer.start_generation(
                name="test",
                model="gemini-2.5-flash",
                prompt="Test prompt",
                model_parameters={},
                metadata={},
            )

        assert ctx is None

    def test_observer_auth_check_fails(self):
        """Observer should handle auth check failure gracefully."""
        mock_langfuse = MagicMock()
        mock_client = MagicMock()
        mock_client.auth_check.return_value = False
        mock_langfuse.Langfuse.return_value = mock_client

        with patch.dict(sys.modules, {"langfuse": mock_langfuse}):
            observer = LangfuseObserver(enabled=True)
            observer._client = None

            ctx = observer.start_generation(
                name="test",
                model="gemini-2.5-flash",
                prompt="Test prompt",
                model_parameters={},
                metadata={},
            )

        assert ctx is None

    def test_start_generation_success(self):
        """Observer should create generation context on success."""
        mock_langfuse = MagicMock()
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_span = MagicMock()
        mock_span.trace_id = "trace-123"
        mock_client.start_span.return_value = mock_span
        mock_langfuse.Langfuse.return_value = mock_client

        with patch.dict(sys.modules, {"langfuse": mock_langfuse}):
            observer = LangfuseObserver(enabled=True)
            observer._client = mock_client

            ctx = observer.start_generation(
                name="gemini-extraction",
                model="gemini-2.5-flash",
                prompt="Extract invoice data",
                model_parameters={"temperature": 0.1},
                metadata={"provider": "gemini", "image_count": 2},
            )

        assert ctx is not None
        assert ctx.trace_id == "trace-123"
        assert ctx.name == "gemini-extraction"
        assert ctx.model == "gemini-2.5-flash"
        mock_client.start_span.assert_called_once()

    def test_end_generation_success(self):
        """Observer should end generation with output and usage for cost tracking."""
        mock_span = MagicMock()

        ctx = GenerationContext(
            trace_id="trace-123",
            span_id="span-789",
            generation_id="gen-456",
            start_time=0.0,
            name="test-generation",
            model="gemini-2.5-flash",
            _span=mock_span,
        )

        observer = LangfuseObserver(enabled=True)
        observer.end_generation(
            ctx=ctx,
            output='{"invoice_id": "INV-001"}',
            input_tokens=100,
            output_tokens=50,
            success=True,
        )

        mock_span.update.assert_called_once()
        mock_span.end.assert_called_once()
        call_kwargs = mock_span.update.call_args.kwargs
        assert call_kwargs["output"]["success"] is True
        # Tokens now in usage dict for LangFuse cost tracking
        assert call_kwargs["usage"]["input"] == 100
        assert call_kwargs["usage"]["output"] == 50
        assert call_kwargs["usage"]["total"] == 150
        assert call_kwargs["usage"]["unit"] == "TOKENS"
        assert call_kwargs["model"] == "gemini-2.5-flash"

    def test_end_generation_with_error(self):
        """Observer should record error on failed generation."""
        mock_span = MagicMock()

        ctx = GenerationContext(
            trace_id="trace-123",
            span_id="span-789",
            generation_id="gen-456",
            start_time=0.0,
            name="test-generation",
            model="gemini-2.5-flash",
            _span=mock_span,
        )

        observer = LangfuseObserver(enabled=True)
        observer.end_generation(
            ctx=ctx,
            output=None,
            input_tokens=None,
            output_tokens=None,
            success=False,
            error_message="API rate limit exceeded",
        )

        mock_span.update.assert_called_once()
        call_kwargs = mock_span.update.call_args.kwargs
        assert call_kwargs["output"]["success"] is False
        assert call_kwargs["level"] == "ERROR"
        assert call_kwargs["status_message"] == "API rate limit exceeded"

    def test_end_generation_with_none_ctx(self):
        """Observer should handle None context gracefully."""
        observer = LangfuseObserver(enabled=True)

        observer.end_generation(
            ctx=None,
            output="test",
            input_tokens=100,
            output_tokens=50,
            success=True,
        )

    def test_score_extraction(self):
        """Observer should attach score to span."""
        mock_span = MagicMock()

        ctx = GenerationContext(
            trace_id="trace-123",
            span_id="span-789",
            generation_id="gen-456",
            start_time=0.0,
            name="test-generation",
            model="gemini-2.5-flash",
            _span=mock_span,
        )

        observer = LangfuseObserver(enabled=True)
        observer.score_extraction(
            ctx=ctx,
            confidence=0.95,
            comment="All fields validated",
        )

        mock_span.score.assert_called_once_with(
            name="extraction_confidence",
            value=0.95,
            data_type="NUMERIC",
            comment="All fields validated",
        )

    def test_score_extraction_with_none_ctx(self):
        """Observer should handle None context gracefully for scoring."""
        observer = LangfuseObserver(enabled=True)
        observer.score_extraction(ctx=None, confidence=0.9)

    def test_flush(self):
        """Observer should flush pending events."""
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True

        observer = LangfuseObserver(enabled=True)
        observer._client = mock_client
        observer.flush()

        mock_client.flush.assert_called_once()

    def test_flush_disabled(self):
        """Observer should not raise when flushing disabled observer."""
        observer = LangfuseObserver(enabled=False)
        observer.flush()

    def test_silent_fallback_on_exception(self):
        """Observer should log warning but not raise on SDK exceptions."""
        mock_langfuse = MagicMock()
        mock_client = MagicMock()
        mock_client.auth_check.return_value = True
        mock_client.start_span.side_effect = Exception("Network error")
        mock_langfuse.Langfuse.return_value = mock_client

        with patch.dict(sys.modules, {"langfuse": mock_langfuse}):
            observer = LangfuseObserver(enabled=True)
            observer._client = mock_client

            ctx = observer.start_generation(
                name="test",
                model="gemini-2.5-flash",
                prompt="Test",
                model_parameters={},
                metadata={},
            )

        assert ctx is None


class TestCreateObserver:
    """Tests for create_observer factory function."""

    def test_create_observer_with_explicit_enabled(self):
        """Factory should respect explicit enabled parameter."""
        observer = create_observer(enabled=False)
        assert observer._enabled is False

        observer = create_observer(enabled=True)
        assert observer._enabled is True

    @patch.dict("os.environ", {"LANGFUSE_PUBLIC_KEY": "pk-123", "LANGFUSE_SECRET_KEY": "sk-456"})
    def test_create_observer_auto_enabled_with_keys(self):
        """Factory should auto-enable when env vars present."""
        observer = create_observer()
        assert observer._enabled is True

    @patch.dict("os.environ", {}, clear=True)
    def test_create_observer_auto_disabled_without_keys(self):
        """Factory should auto-disable when env vars missing."""
        observer = create_observer()
        assert observer._enabled is False


class TestGenerationContext:
    """Tests for GenerationContext dataclass."""

    def test_generation_context_creation(self):
        """GenerationContext should store all fields."""
        ctx = GenerationContext(
            trace_id="trace-abc",
            span_id="span-def",
            generation_id="gen-123",
            start_time=1234567890.123,
            name="test-generation",
            model="gemini-2.5-flash",
        )

        assert ctx.trace_id == "trace-abc"
        assert ctx.span_id == "span-def"
        assert ctx.generation_id == "gen-123"
        assert ctx.start_time == 1234567890.123
        assert ctx.name == "test-generation"
        assert ctx.model == "gemini-2.5-flash"


class TestTraceContext:
    """Tests for TraceContext dataclass."""

    def test_trace_context_creation(self):
        """TraceContext should store distributed tracing fields."""
        ctx = TraceContext(
            trace_id="abcd1234567890abcd1234567890ab",
            session_id="session-123",
            parent_span_id="fedcba0987654321",
        )

        assert ctx.trace_id == "abcd1234567890abcd1234567890ab"
        assert ctx.session_id == "session-123"
        assert ctx.parent_span_id == "fedcba0987654321"

    def test_trace_context_from_message(self):
        """TraceContext should be created from message with trace fields."""
        mock_message = MagicMock()
        mock_message.trace_id = "trace-from-message"
        mock_message.session_id = "session-from-message"
        mock_message.parent_span_id = "parent-span-id"

        ctx = TraceContext.from_message(mock_message)

        assert ctx.trace_id == "trace-from-message"
        assert ctx.session_id == "session-from-message"
        assert ctx.parent_span_id == "parent-span-id"


class TestPromptResult:
    """Tests for PromptResult dataclass."""

    def test_prompt_result_from_langfuse(self):
        """PromptResult should store LangFuse prompt info."""
        result = PromptResult(
            content="Extract invoice data from the image.",
            name="extraction-grubhub",
            version=3,
            is_fallback=False,
        )

        assert result.content == "Extract invoice data from the image."
        assert result.name == "extraction-grubhub"
        assert result.version == 3
        assert result.is_fallback is False

    def test_prompt_result_fallback(self):
        """PromptResult should indicate fallback mode."""
        result = PromptResult(
            content="Local prompt content",
            name="local-grubhub",
            version=None,
            is_fallback=True,
        )

        assert result.is_fallback is True
        assert result.version is None
