"""Unit tests for function timing utilities."""

import time

import pytest

from shared.utils.timing import function_timer


class TestFunctionTimer:
    """Tests for function_timer context manager."""

    def test_function_timer_returns_positive_latency(self) -> None:
        """Timer should return positive milliseconds for any work."""
        with function_timer() as timing:
            time.sleep(0.01)  # 10ms

        assert "latency_ms" in timing
        assert timing["latency_ms"] >= 10

    def test_function_timer_captures_exception_time(self) -> None:
        """Timer should still capture time even when exception is raised."""
        with pytest.raises(ValueError):
            with function_timer() as timing:
                time.sleep(0.005)  # 5ms
                raise ValueError("test error")

        assert "latency_ms" in timing
        assert timing["latency_ms"] >= 5

    def test_function_timer_millisecond_precision(self) -> None:
        """Timer should return an integer value in milliseconds."""
        with function_timer() as timing:
            pass

        assert isinstance(timing["latency_ms"], int)

    def test_function_timer_empty_dict_during_context(self) -> None:
        """Timer dict should be empty during context execution."""
        captured_during = None

        with function_timer() as timing:
            captured_during = dict(timing)

        assert captured_during == {}
        assert timing["latency_ms"] >= 0

    def test_function_timer_zero_or_more_for_fast_operations(self) -> None:
        """Timer should return >= 0 even for very fast operations."""
        with function_timer() as timing:
            x = 1 + 1  # Very fast operation

        assert timing["latency_ms"] >= 0

    def test_function_timer_multiple_uses(self) -> None:
        """Timer can be used multiple times independently."""
        with function_timer() as timing1:
            time.sleep(0.01)

        with function_timer() as timing2:
            time.sleep(0.02)

        assert timing1["latency_ms"] >= 10
        assert timing2["latency_ms"] >= 20
        assert timing2["latency_ms"] > timing1["latency_ms"]

    def test_function_timer_nested_contexts(self) -> None:
        """Nested timers should work independently."""
        with function_timer() as outer:
            time.sleep(0.01)
            with function_timer() as inner:
                time.sleep(0.01)

        assert inner["latency_ms"] >= 10
        assert outer["latency_ms"] >= inner["latency_ms"]

    def test_function_timer_dict_is_mutable(self) -> None:
        """Timer dict should be mutable for adding custom metrics."""
        with function_timer() as timing:
            timing["custom_metric"] = 42

        assert timing["custom_metric"] == 42
        assert "latency_ms" in timing
