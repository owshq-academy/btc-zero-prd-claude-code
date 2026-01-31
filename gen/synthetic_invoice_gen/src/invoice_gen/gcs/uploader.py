"""GCS upload functionality for generated invoices."""

from dataclasses import dataclass
from pathlib import Path

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError


@dataclass
class UploadResult:
    """Result of a single file upload attempt."""

    local_path: Path
    gcs_uri: str | None
    success: bool
    error: str | None = None


class GCSUploader:
    """Handles uploading files to Google Cloud Storage."""

    def __init__(self, bucket_name: str):
        """Initialize uploader with target bucket.

        Args:
            bucket_name: GCS bucket name (without gs:// prefix)

        Raises:
            ValueError: If bucket is empty
            GoogleCloudError: If bucket doesn't exist or not accessible
        """
        if not bucket_name:
            raise ValueError("Bucket name cannot be empty")

        self.bucket_name = bucket_name
        self._client = storage.Client()
        self._bucket = self._client.bucket(bucket_name)

        if not self._bucket.exists():
            raise GoogleCloudError(f"Bucket '{bucket_name}' does not exist or is not accessible")

    def upload_file(self, local_path: Path) -> UploadResult:
        """Upload a single file to GCS.

        Args:
            local_path: Path to local file

        Returns:
            UploadResult with success/failure details
        """
        blob_name = local_path.name
        gcs_uri = f"gs://{self.bucket_name}/{blob_name}"

        try:
            blob = self._bucket.blob(blob_name)
            blob.upload_from_filename(
                str(local_path),
                content_type="image/tiff",
                timeout=300,
            )
            return UploadResult(
                local_path=local_path,
                gcs_uri=gcs_uri,
                success=True,
            )
        except GoogleCloudError as e:
            return UploadResult(
                local_path=local_path,
                gcs_uri=None,
                success=False,
                error=str(e),
            )
