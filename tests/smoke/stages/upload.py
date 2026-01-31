"""Stage 2: Upload generated TIFF to GCS landing bucket."""

from tests.smoke.config import load_config
from tests.smoke.models import SmokeContext
from tests.smoke.stages.base import Stage, StageResult

try:
    from google.cloud import storage

    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


class UploadStage(Stage):
    """Upload the generated TIFF invoice to GCS.

    This stage:
    1. Connects to GCS using application default credentials
    2. Uploads the TIFF to the landing folder
    3. Stores the GCS object path in context for downstream stages
    """

    name = "upload"

    def run(self, context: SmokeContext) -> StageResult:
        """Upload TIFF to GCS landing bucket."""
        if not GCS_AVAILABLE:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error="google-cloud-storage not installed. Run: pip install google-cloud-storage",
            )

        if not context.tiff_path or not context.tiff_path.exists():
            return StageResult(
                stage_name=self.name,
                passed=False,
                error=f"TIFF file not found: {context.tiff_path}",
            )

        # Load config for bucket and folder
        config = load_config()
        env_config = config.environments.get(context.env)
        if not env_config:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error=f"Unknown environment: {context.env}",
            )

        stage_config = config.get_stage("upload")
        landing_folder = stage_config.folder or "landing"

        # Build GCS path
        bucket_name = env_config.bucket
        blob_name = f"{landing_folder}/{context.tiff_path.name}"

        # Upload to GCS
        client = storage.Client(project=env_config.project)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        blob.upload_from_filename(str(context.tiff_path))

        # Store GCS path in context
        context.gcs_object_path = f"gs://{bucket_name}/{blob_name}"

        return StageResult(
            stage_name=self.name,
            passed=True,
            data={
                "bucket": bucket_name,
                "blob": blob_name,
                "gcs_uri": context.gcs_object_path,
            },
        )
