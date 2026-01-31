"""Stage 3: Poll BigQuery for extraction completion."""

import time

from tests.smoke.config import load_config
from tests.smoke.models import SmokeContext
from tests.smoke.stages.base import Stage, StageResult

try:
    from google.cloud import bigquery

    BQ_AVAILABLE = True
except ImportError:
    BQ_AVAILABLE = False


class ProcessStage(Stage):
    """Poll BigQuery to verify pipeline processing completed.

    This stage:
    1. Polls BigQuery for the extracted invoice row
    2. Waits with configurable timeout and poll interval
    3. Loads the extracted data into context for validation
    """

    name = "process"

    def run(self, context: SmokeContext) -> StageResult:
        """Poll BigQuery for extraction completion."""
        if not BQ_AVAILABLE:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error="google-cloud-bigquery not installed",
            )

        if not context.invoice_data:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error="No invoice_data in context. Generate stage must run first.",
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

        stage_config = config.get_stage("process")
        timeout_seconds = stage_config.timeout_seconds or 120
        poll_interval = stage_config.poll_interval_seconds or 5

        bq_config = config.get_stage("bigquery")
        table_name = bq_config.table or "extracted_invoices"

        # Get invoice_id from ground truth
        invoice_id = context.invoice_data.get("invoice_id", "unknown")

        # Build table reference
        table_ref = f"{env_config.project}.{env_config.dataset}.{table_name}"

        # Poll BigQuery for the row
        client = bigquery.Client(project=env_config.project)

        query = f"""
            SELECT invoice_id, vendor_type, total_amount, currency
            FROM `{table_ref}`
            WHERE invoice_id = @invoice_id
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("invoice_id", "STRING", invoice_id)
            ]
        )

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                results = client.query(query, job_config=job_config).result()
                rows = list(results)

                if rows:
                    # Found! Load extracted data into context
                    row = rows[0]
                    context.extracted_data = {
                        "invoice_id": row.invoice_id,
                        "vendor_type": row.vendor_type,
                        "total_amount": float(row.total_amount) if row.total_amount else None,
                        "currency": row.currency,
                    }

                    wait_time = round(time.time() - start_time, 1)
                    return StageResult(
                        stage_name=self.name,
                        passed=True,
                        data={
                            "invoice_id": invoice_id,
                            "wait_time_seconds": wait_time,
                            "table": table_ref,
                        },
                    )
            except Exception as e:
                # Query failed, continue polling
                pass

            time.sleep(poll_interval)

        # Timeout reached
        return StageResult(
            stage_name=self.name,
            passed=False,
            error=f"Timeout after {timeout_seconds}s waiting for invoice in BigQuery: {invoice_id}",
            data={"invoice_id": invoice_id, "table": table_ref},
        )
