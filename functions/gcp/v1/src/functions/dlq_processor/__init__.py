"""DLQ Processor - Handles failed messages from dead-letter queues."""

from .main import handle_dlq_message

__all__ = ["handle_dlq_message"]
