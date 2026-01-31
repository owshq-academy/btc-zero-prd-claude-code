include "root" {
  path = find_in_parent_folders()
}

include "env" {
  path   = find_in_parent_folders("env.hcl")
  expose = true
}

dependency "iam" {
  config_path = "../iam"
  mock_outputs = {
    service_account_emails = {
      tiff_converter     = "mock-sa@example.iam.gserviceaccount.com"
      classifier         = "mock-sa@example.iam.gserviceaccount.com"
      extractor          = "mock-sa@example.iam.gserviceaccount.com"
      bq_writer          = "mock-sa@example.iam.gserviceaccount.com"
      pubsub_invoker     = "mock-sa@example.iam.gserviceaccount.com"
    }
  }
}

dependency "pubsub" {
  config_path = "../pubsub"
  mock_outputs = {
    topic_ids = {
      invoice_uploaded   = "projects/mock/topics/invoice-uploaded"
      invoice_converted  = "projects/mock/topics/invoice-converted"
      invoice_classified = "projects/mock/topics/invoice-classified"
      invoice_extracted  = "projects/mock/topics/invoice-extracted"
      raw_gemini_output  = "projects/mock/topics/raw-gemini-output"
    }
  }
}

dependency "gcs" {
  config_path = "../gcs"
  mock_outputs = {
    bucket_names = {
      pipeline  = "mock-pipeline-bucket"
      processed = "mock-processed-bucket"
      archive   = "mock-archive-bucket"
      failed    = "mock-failed-bucket"
    }
  }
}

dependency "secrets" {
  config_path = "../secrets"
  mock_outputs = {
    secret_ids = {
      gemini_api_key     = "mock-gemini-secret"
      openrouter_api_key = "mock-openrouter-secret"
      langfuse_secret    = "mock-langfuse-secret"
    }
  }
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//cloud-run"
}

inputs = {
  # Use placeholder image for initial infrastructure deployment
  # Set to false once actual container images are built and pushed
  use_placeholder_image = true

  services = {
    tiff_converter = include.env.locals.cloud_run_settings.tiff_converter
    invoice_classifier = include.env.locals.cloud_run_settings.invoice_classifier
    data_extractor = include.env.locals.cloud_run_settings.data_extractor
    bigquery_writer = include.env.locals.cloud_run_settings.bigquery_writer
  }

  service_accounts = {
    tiff_converter     = dependency.iam.outputs.service_account_emails["tiff_converter"]
    invoice_classifier = dependency.iam.outputs.service_account_emails["classifier"]
    data_extractor     = dependency.iam.outputs.service_account_emails["extractor"]
    bigquery_writer    = dependency.iam.outputs.service_account_emails["bq_writer"]
  }

  pubsub_topics = dependency.pubsub.outputs.topic_ids
  gcs_buckets   = dependency.gcs.outputs.bucket_names
  secrets       = dependency.secrets.outputs.secret_ids

  invoker_service_account = dependency.iam.outputs.service_account_emails["pubsub_invoker"]
}
