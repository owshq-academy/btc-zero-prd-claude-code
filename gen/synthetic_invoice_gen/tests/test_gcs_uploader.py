"""Tests for GCS uploader."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from google.cloud.exceptions import GoogleCloudError

from invoice_gen.gcs.uploader import GCSUploader, UploadResult


class TestUploadResult:
    def test_upload_result_success(self) -> None:
        result = UploadResult(
            local_path=Path("/tmp/test.tiff"),
            gcs_uri="gs://bucket/test.tiff",
            success=True,
        )
        assert result.success is True
        assert result.gcs_uri == "gs://bucket/test.tiff"
        assert result.error is None

    def test_upload_result_failure(self) -> None:
        result = UploadResult(
            local_path=Path("/tmp/test.tiff"),
            gcs_uri=None,
            success=False,
            error="Permission denied",
        )
        assert result.success is False
        assert result.gcs_uri is None
        assert result.error == "Permission denied"


class TestGCSUploaderInit:
    def test_empty_bucket_name_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Bucket name cannot be empty"):
            GCSUploader("")

    @patch("invoice_gen.gcs.uploader.storage.Client")
    def test_init_validates_bucket_exists(self, mock_client_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.exists.return_value = True
        mock_client.bucket.return_value = mock_bucket
        mock_client_class.return_value = mock_client

        uploader = GCSUploader("test-bucket")

        mock_client.bucket.assert_called_once_with("test-bucket")
        mock_bucket.exists.assert_called_once()
        assert uploader.bucket_name == "test-bucket"

    @patch("invoice_gen.gcs.uploader.storage.Client")
    def test_init_raises_on_nonexistent_bucket(self, mock_client_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.exists.return_value = False
        mock_client.bucket.return_value = mock_bucket
        mock_client_class.return_value = mock_client

        with pytest.raises(GoogleCloudError, match="does not exist"):
            GCSUploader("nonexistent-bucket")


class TestGCSUploaderUpload:
    @patch("invoice_gen.gcs.uploader.storage.Client")
    def test_upload_file_success(self, mock_client_class: MagicMock, tmp_path: Path) -> None:
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob
        mock_client.bucket.return_value = mock_bucket
        mock_client_class.return_value = mock_client

        test_file = tmp_path / "ubereats_INV-123_20260130.tiff"
        test_file.write_bytes(b"fake tiff content")

        uploader = GCSUploader("test-bucket")
        result = uploader.upload_file(test_file)

        assert result.success is True
        assert result.gcs_uri == "gs://test-bucket/ubereats_INV-123_20260130.tiff"
        assert result.error is None
        mock_blob.upload_from_filename.assert_called_once_with(
            str(test_file),
            content_type="image/tiff",
            timeout=300,
        )

    @patch("invoice_gen.gcs.uploader.storage.Client")
    def test_upload_file_failure_returns_error(
        self, mock_client_class: MagicMock, tmp_path: Path
    ) -> None:
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob
        mock_blob.upload_from_filename.side_effect = GoogleCloudError("Upload failed")
        mock_client.bucket.return_value = mock_bucket
        mock_client_class.return_value = mock_client

        test_file = tmp_path / "test.tiff"
        test_file.write_bytes(b"fake tiff content")

        uploader = GCSUploader("test-bucket")
        result = uploader.upload_file(test_file)

        assert result.success is False
        assert result.gcs_uri is None
        assert "Upload failed" in result.error

    @patch("invoice_gen.gcs.uploader.storage.Client")
    def test_upload_uses_filename_only(self, mock_client_class: MagicMock, tmp_path: Path) -> None:
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob
        mock_client.bucket.return_value = mock_bucket
        mock_client_class.return_value = mock_client

        nested_dir = tmp_path / "nested" / "path"
        nested_dir.mkdir(parents=True)
        test_file = nested_dir / "invoice.tiff"
        test_file.write_bytes(b"fake tiff content")

        uploader = GCSUploader("bucket")
        result = uploader.upload_file(test_file)

        assert result.gcs_uri == "gs://bucket/invoice.tiff"
        mock_bucket.blob.assert_called_with("invoice.tiff")
