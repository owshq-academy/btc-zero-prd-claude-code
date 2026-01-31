"""Stage 5: Verify extraction landed in BigQuery."""

from tests.smoke.config import load_config
from tests.smoke.models import SmokeContext
from tests.smoke.stages.base import Stage, StageResult

try:
    from google.cloud import bigquery

    BQ_AVAILABLE = True
except ImportError:
    BQ_AVAILABLE = False


class BigQueryStage(Stage):
    """Verify the extraction record exists in BigQuery.

    This stage:
    1. Queries the extractions table for the invoice_id
    2. Verifies the row was written successfully
    3. Optionally validates key fields match
    """

    name = "bigquery"

    def run(self, context: SmokeContext) -> StageResult:
        """Query BigQuery for the extraction record."""
        if not BQ_AVAILABLE:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error="google-cloud-bigquery not installed. Run: pip install google-cloud-bigquery",
            )

        if not context.invoice_data:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error="No invoice_data in context",
            )

        invoice_id = context.invoice_data.get("invoice_id")
        if not invoice_id:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error="No invoice_id in invoice_data",
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

        stage_config = config.get_stage("bigquery")
        table_name = stage_config.table or "extractions"

        # Build fully qualified table name
        table_ref = f"{env_config.project}.{env_config.dataset}.{table_name}"

        # Query for the record
        client = bigquery.Client(project=env_config.project)

        query = f"""
            SELECT invoice_id, vendor_type, total_amount, currency, created_at
            FROM `{table_ref}`
            WHERE invoice_id = @invoice_id
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("invoice_id", "STRING", invoice_id)
            ]
        )

        results = client.query(query, job_config=job_config).result()
        rows = list(results)

        if not rows:
            context.bq_row_found = False
            return StageResult(
                stage_name=self.name,
                passed=False,
                error=f"No row found in BigQuery for invoice_id: {invoice_id}",
                data={"table": table_ref, "invoice_id": invoice_id},
            )

        # Row found
        context.bq_row_found = True
        row = rows[0]

        return StageResult(
            stage_name=self.name,
            passed=True,
            data={
                "table": table_ref,
                "invoice_id": row.invoice_id,
                "vendor_type": row.vendor_type,
                "total_amount": float(row.total_amount) if row.total_amount else None,
            },
        )
