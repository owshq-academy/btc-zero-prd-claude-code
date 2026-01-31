"""Function timing utilities for observability.

Provides context managers for measuring function execution time
with consistent field naming for Cloud Logging.
"""

import time
from contextlib import contextmanager
from typing import Generator


@contextmanager
def function_timer() -> Generator[dict[str, int], None, None]:
    """Context manager for measuring function execution time.

    Yields a mutable dict that will contain 'latency_ms' after the context exits.
    The dict can be included in log extra fields.

    Example:
        with function_timer() as timing:
            # ... do work ...

        logger.info("Complete", extra={"latency_ms": timing["latency_ms"]})

    Yields:
        Dict with 'latency_ms' key (populated on exit)
    """
    metrics: dict[str, int] = {}
    start = time.perf_counter()
    try:
        yield metrics
    finally:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        metrics["latency_ms"] = elapsed_ms
