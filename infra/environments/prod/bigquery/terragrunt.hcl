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
      bq_writer = "mock-sa@example.iam.gserviceaccount.com"
    }
  }
  skip_outputs = true
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//bigquery"
}

inputs = {
  dataset_id                = include.env.locals.bigquery_config.dataset_id
  location                  = include.env.locals.bigquery_config.location
  partition_expiration_days = include.env.locals.bigquery_config.partition_expiration_days
}
