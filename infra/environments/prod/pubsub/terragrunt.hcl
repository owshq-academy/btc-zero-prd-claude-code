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
      pubsub_invoker = "mock-sa@example.iam.gserviceaccount.com"
    }
  }
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//pubsub"
}

inputs = {
  topics                  = include.env.locals.pubsub_topics
  invoker_service_account = dependency.iam.outputs.service_account_emails["pubsub_invoker"]
}
