locals {
  environment = "prod"
  project_id  = "eda-gemini-prd"
  region      = "us-central1"

  cloud_run_settings = {
    tiff_converter = {
      memory        = "1Gi"
      cpu           = "1"
      timeout       = 300
      min_instances = 1
      max_instances = 50
      concurrency   = 1
    }
    invoice_classifier = {
      memory        = "512Mi"
      cpu           = "1"
      timeout       = 120
      min_instances = 1
      max_instances = 50
      concurrency   = 10
    }
    data_extractor = {
      memory        = "2Gi"
      cpu           = "2"
      timeout       = 300
      min_instances = 2
      max_instances = 100
      concurrency   = 1
    }
    bigquery_writer = {
      memory        = "512Mi"
      cpu           = "1"
      timeout       = 60
      min_instances = 1
      max_instances = 50
      concurrency   = 50
    }
  }

  secrets_config = {
    gemini_api_key = {
      secret_id   = "eda-gemini-prd-gemini-api-key"
      description = "Vertex AI / Gemini API Key"
    }
    openrouter_api_key = {
      secret_id   = "eda-gemini-prd-openrouter-api-key"
      description = "OpenRouter fallback API Key"
    }
    langfuse_secret = {
      secret_id   = "eda-gemini-prd-langfuse-secret"
      description = "LangFuse observability credentials"
    }
  }

  service_accounts = {
    tiff_converter = {
      account_id   = "sa-tiff-converter-prd"
      display_name = "TIFF Converter Service Account"
      roles = [
        "roles/storage.objectViewer",
        "roles/storage.objectCreator",
        "roles/pubsub.publisher"
      ]
    }
    classifier = {
      account_id   = "sa-classifier-prd"
      display_name = "Invoice Classifier Service Account"
      roles = [
        "roles/storage.objectViewer",
        "roles/storage.objectCreator",
        "roles/pubsub.publisher"
      ]
    }
    extractor = {
      account_id   = "sa-extractor-prd"
      display_name = "Data Extractor Service Account"
      roles = [
        "roles/storage.objectViewer",
        "roles/storage.objectCreator",
        "roles/pubsub.publisher",
        "roles/aiplatform.user",
        "roles/secretmanager.secretAccessor"
      ]
    }
    bq_writer = {
      account_id   = "sa-bq-writer-prd"
      display_name = "BigQuery Writer Service Account"
      roles = [
        "roles/bigquery.dataEditor",
        "roles/storage.objectViewer"
      ]
    }
    pubsub_invoker = {
      account_id   = "sa-pubsub-invoker-prd"
      display_name = "Pub/Sub Invoker Service Account"
      roles = [
        "roles/run.invoker"
      ]
    }
  }

  gcs_buckets = {
    pipeline = {
      name                 = "eda-gemini-prd-pipeline"
      location             = "US"
      storage_class        = "STANDARD"
      lifecycle_age_days   = 90
      enable_notification  = true
      notification_prefix  = "landing/"
    }
    processed = {
      name                 = "eda-gemini-prd-processed"
      location             = "US"
      storage_class        = "STANDARD"
      lifecycle_age_days   = 90
      enable_notification  = false
      notification_prefix  = null
    }
    archive = {
      name                 = "eda-gemini-prd-archive"
      location             = "US"
      storage_class        = "NEARLINE"
      lifecycle_age_days   = 2555
      enable_notification  = false
      notification_prefix  = null
    }
    failed = {
      name                 = "eda-gemini-prd-failed"
      location             = "US"
      storage_class        = "STANDARD"
      lifecycle_age_days   = null
      enable_notification  = false
      notification_prefix  = null
    }
  }

  pubsub_topics = {
    invoice_uploaded = {
      name                       = "eda-gemini-prd-invoice-uploaded"
      message_retention_duration = "604800s"
      enable_dlq                 = true
    }
    invoice_converted = {
      name                       = "eda-gemini-prd-invoice-converted"
      message_retention_duration = "604800s"
      enable_dlq                 = true
    }
    invoice_classified = {
      name                       = "eda-gemini-prd-invoice-classified"
      message_retention_duration = "604800s"
      enable_dlq                 = true
    }
    invoice_extracted = {
      name                       = "eda-gemini-prd-invoice-extracted"
      message_retention_duration = "604800s"
      enable_dlq                 = true
    }
    raw_gemini_output = {
      name                       = "eda-gemini-prd-raw-gemini-output"
      message_retention_duration = "604800s"
      enable_dlq                 = false
    }
  }

  bigquery_config = {
    dataset_id          = "ds_bq_gemini_prd"
    location            = "US"
    partition_expiration_days = null
  }

  enable_dead_letter_queues = true
}
