"""Stage 6: Check Cloud Logging for errors."""

from datetime import datetime, timedelta, timezone

from tests.smoke.config import load_config
from tests.smoke.models import SmokeContext
from tests.smoke.stages.base import Stage, StageResult

try:
    from google.cloud import logging as cloud_logging

    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False


class LoggingStage(Stage):
    """Check Cloud Logging for pipeline errors.

    This stage:
    1. Queries Cloud Logging for recent ERROR/CRITICAL logs
    2. Filters by the invoice_id if available
    3. Reports any errors found during processing
    """

    name = "logging"

    def run(self, context: SmokeContext) -> StageResult:
        """Query Cloud Logging for pipeline errors."""
        if not LOGGING_AVAILABLE:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error="google-cloud-logging not installed. Run: pip install google-cloud-logging",
            )

        # Load config
        config = load_config()
        env_config = config.environments.get(context.env)
        if not env_config:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error=f"Unknown environment: {context.env}",
            )

        stage_config = config.get_stage("logging")
        lookback_minutes = stage_config.lookback_minutes or 5
        severity_threshold = stage_config.severity_threshold or "ERROR"

        # Build filter
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(minutes=lookback_minutes)
        timestamp_filter = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Build log filter
        filter_parts = [
            f'resource.type="cloud_run_revision"',
            f'timestamp>="{timestamp_filter}"',
            f'severity>={severity_threshold}',
        ]

        # Add invoice_id filter if available
        invoice_id = context.invoice_data.get("invoice_id") if context.invoice_data else None
        if invoice_id:
            filter_parts.append(f'textPayload:"{invoice_id}" OR jsonPayload.invoice_id="{invoice_id}"')

        log_filter = " AND ".join(filter_parts)

        # Query logs
        client = cloud_logging.Client(project=env_config.project)
        entries = list(client.list_entries(filter_=log_filter, max_results=10))

        # Process results
        errors = []
        for entry in entries:
            error_msg = entry.payload if isinstance(entry.payload, str) else str(entry.payload)
            errors.append({
                "timestamp": str(entry.timestamp),
                "severity": entry.severity,
                "message": error_msg[:200],  # Truncate long messages
            })

        context.log_errors_found = [e["message"] for e in errors]

        if errors:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error=f"Found {len(errors)} error(s) in Cloud Logging",
                data={
                    "error_count": len(errors),
                    "errors": errors[:5],  # Limit to first 5
                    "filter": log_filter,
                },
            )

        return StageResult(
            stage_name=self.name,
            passed=True,
            data={
                "lookback_minutes": lookback_minutes,
                "errors_found": 0,
            },
        )
