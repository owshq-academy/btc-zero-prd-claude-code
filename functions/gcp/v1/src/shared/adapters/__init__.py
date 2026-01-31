"""Protocol-based adapters for GCP services.

These adapters enable:
- Unit testing with mock implementations
- Dependency injection for flexibility
- Clear contracts between layers
"""

from shared.adapters.bigquery import BigQueryAdapter, GCPBigQueryAdapter
from shared.adapters.llm import GeminiAdapter, LLMAdapter, LLMResponse, OpenRouterAdapter
from shared.adapters.messaging import MessagingAdapter, PubSubAdapter
from shared.adapters.observability import (
    GenerationContext,
    LangfuseObserver,
    PromptResult,
    TraceContext,
    create_observer,
)
from shared.adapters.storage import GCSAdapter, StorageAdapter

__all__ = [
    "StorageAdapter",
    "GCSAdapter",
    "MessagingAdapter",
    "PubSubAdapter",
    "LLMAdapter",
    "GeminiAdapter",
    "OpenRouterAdapter",
    "LLMResponse",
    "BigQueryAdapter",
    "GCPBigQueryAdapter",
    "LangfuseObserver",
    "GenerationContext",
    "TraceContext",
    "PromptResult",
    "create_observer",
]
