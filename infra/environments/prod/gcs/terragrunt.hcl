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
      invoice_uploaded = "projects/mock/topics/mock"
    }
  }
  skip_outputs = true
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//gcs"
}

inputs = {
  buckets               = include.env.locals.gcs_buckets
  notification_topic_id = null
}
