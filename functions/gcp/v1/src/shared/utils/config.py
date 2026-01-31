"""Application configuration from environment variables.

Uses dataclass for immutability and lru_cache for singleton pattern.
All configuration is derived from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Config:
    """Application configuration from environment variables.

    Attributes:
        project_id: GCP project ID
        region: GCP region for Vertex AI
        input_bucket: GCS bucket for raw TIFFs
        processed_bucket: GCS bucket for converted PNGs
        archive_bucket: GCS bucket for archived originals
        failed_bucket: GCS bucket for failed extractions
        uploaded_topic: Pub/Sub topic for file uploads
        converted_topic: Pub/Sub topic for converted files
        classified_topic: Pub/Sub topic for classified invoices
        extracted_topic: Pub/Sub topic for extracted data
        gemini_model: Vertex AI model name
        openrouter_api_key: OpenRouter API key (fallback)
        dataset: BigQuery dataset name
        invoices_table: BigQuery invoices table
        line_items_table: BigQuery line items table
        langfuse_public_key: LangFuse public API key
        langfuse_secret_key: LangFuse secret key (from Secret Manager)
        langfuse_base_url: LangFuse server endpoint
        langfuse_enabled: Whether LangFuse observability is enabled
    """

    project_id: str
    region: str
    input_bucket: str
    processed_bucket: str
    archive_bucket: str
    failed_bucket: str
    uploaded_topic: str
    converted_topic: str
    classified_topic: str
    extracted_topic: str
    gemini_model: str
    openrouter_api_key: str | None
    dataset: str
    invoices_table: str
    line_items_table: str
    metrics_table: str
    langfuse_public_key: str | None
    langfuse_secret_key: str | None
    langfuse_base_url: str
    langfuse_enabled: bool


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Load configuration from environment (cached).

    Returns:
        Config instance with all settings

    Note:
        Uses lru_cache to ensure singleton pattern.
        Clear cache with get_config.cache_clear() for testing.
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "invoice-pipeline-dev")

    langfuse_public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    langfuse_enabled = bool(langfuse_public_key and langfuse_secret_key)

    return Config(
        project_id=project_id,
        region=os.environ.get("GCP_REGION", "us-central1"),
        input_bucket=os.environ.get("INPUT_BUCKET", f"{project_id}-invoices-input"),
        processed_bucket=os.environ.get("PROCESSED_BUCKET", f"{project_id}-invoices-processed"),
        archive_bucket=os.environ.get("ARCHIVE_BUCKET", f"{project_id}-invoices-archive"),
        failed_bucket=os.environ.get("FAILED_BUCKET", f"{project_id}-invoices-failed"),
        uploaded_topic=os.environ.get("UPLOADED_TOPIC", "invoice-uploaded"),
        converted_topic=os.environ.get("CONVERTED_TOPIC", "invoice-converted"),
        classified_topic=os.environ.get("CLASSIFIED_TOPIC", "invoice-classified"),
        extracted_topic=os.environ.get("EXTRACTED_TOPIC", "invoice-extracted"),
        gemini_model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY"),
        dataset=os.environ.get("BQ_DATASET", "invoices"),
        invoices_table=os.environ.get("BQ_INVOICES_TABLE", "extracted_invoices"),
        line_items_table=os.environ.get("BQ_LINE_ITEMS_TABLE", "line_items"),
        metrics_table=os.environ.get("BQ_METRICS_TABLE", "extraction_metrics"),
        langfuse_public_key=langfuse_public_key,
        langfuse_secret_key=langfuse_secret_key,
        langfuse_base_url=os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
        langfuse_enabled=langfuse_enabled,
    )
