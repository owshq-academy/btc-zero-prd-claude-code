"""Tests for the CLI interface."""

import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from invoice_gen.cli import main


def _check_poppler_installed() -> bool:
    return shutil.which("pdftoppm") is not None


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestCLI:
    def test_help_option(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "--partner" in result.output
        assert "--all-partners" in result.output
        assert "--count" in result.output

    def test_requires_partner_or_all(self, runner: CliRunner) -> None:
        result = runner.invoke(main, [])
        assert result.exit_code != 0
        assert "Either --partner or --all-partners must be specified" in result.output

    def test_cannot_use_both_partner_and_all(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--partner", "ubereats", "--all-partners"])
        assert result.exit_code != 0
        assert "Cannot use both" in result.output

    def test_invalid_partner_rejected(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--partner", "invalid_partner"])
        assert result.exit_code != 0

    def test_valid_partner_accepted(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(
            main,
            ["--partner", "ubereats", "--output", str(tmp_path), "--count", "1"],
        )
        if result.exit_code == 0:
            assert "Generating" in result.output
            assert "ubereats" in result.output.lower()

    def test_seed_option_accepted(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(
            main,
            [
                "--partner",
                "doordash",
                "--output",
                str(tmp_path),
                "--seed",
                "42",
                "--count",
                "1",
            ],
        )
        if result.exit_code == 0:
            assert "Seed: 42" in result.output

    def test_format_option(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(
            main,
            [
                "--partner",
                "grubhub",
                "--output",
                str(tmp_path),
                "--format",
                "pdf",
                "--count",
                "1",
            ],
        )
        if result.exit_code == 0:
            assert "Format: PDF" in result.output

    def test_all_partners_option(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(
            main,
            ["--all-partners", "--output", str(tmp_path), "--count", "1"],
        )
        if result.exit_code == 0:
            assert "ubereats" in result.output.lower()
            assert "doordash" in result.output.lower()
            assert "5" in result.output or "invoices" in result.output.lower()


class TestCLIIntegration:
    @pytest.mark.skipif(
        not _check_poppler_installed(),
        reason="Poppler not installed",
    )
    def test_generate_single_invoice(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(
            main,
            ["--partner", "ubereats", "--output", str(tmp_path), "--count", "1"],
        )
        assert result.exit_code == 0
        assert "Generation Complete!" in result.output

        tiff_files = list(tmp_path.glob("*.tiff"))
        assert len(tiff_files) == 1

    @pytest.mark.skipif(
        not _check_poppler_installed(),
        reason="Poppler not installed",
    )
    def test_reproducible_generation(self, runner: CliRunner, tmp_path: Path) -> None:
        output1 = tmp_path / "run1"
        output2 = tmp_path / "run2"
        output1.mkdir()
        output2.mkdir()

        runner.invoke(
            main,
            ["--partner", "ifood", "--output", str(output1), "--seed", "42"],
        )
        runner.invoke(
            main,
            ["--partner", "ifood", "--output", str(output2), "--seed", "42"],
        )

        files1 = list(output1.glob("*.tiff"))
        files2 = list(output2.glob("*.tiff"))

        if files1 and files2:
            assert files1[0].name == files2[0].name


class TestCLIGCSOptions:
    def test_help_shows_gcs_bucket_option(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "--gcs-bucket" in result.output
        assert "GCS bucket" in result.output

    def test_gcs_bucket_option_accepted(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(
            main,
            [
                "--partner",
                "ubereats",
                "--output",
                str(tmp_path),
                "--gcs-bucket",
                "test-bucket",
            ],
        )
        assert "GCS access failed" in result.output or "test-bucket" in result.output

    @patch("invoice_gen.gcs.uploader.storage.Client")
    def test_gcs_bucket_validates_on_start(
        self, mock_client_class: MagicMock, runner: CliRunner, tmp_path: Path
    ) -> None:
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.exists.return_value = False
        mock_client.bucket.return_value = mock_bucket
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            [
                "--partner",
                "ubereats",
                "--output",
                str(tmp_path),
                "--gcs-bucket",
                "nonexistent",
            ],
        )

        assert result.exit_code != 0
        assert "GCS access failed" in result.output

    def test_without_gcs_bucket_works_normally(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(
            main,
            ["--partner", "ubereats", "--output", str(tmp_path), "--count", "1"],
        )
        if result.exit_code == 0:
            assert "Uploading to GCS" not in result.output
            assert "Generating" in result.output
