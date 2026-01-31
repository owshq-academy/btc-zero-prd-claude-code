include "root" {
  path = find_in_parent_folders()
}

include "env" {
  path   = find_in_parent_folders("env.hcl")
  expose = true
}

dependency "secrets" {
  config_path = "../secrets"
  mock_outputs = {
    secret_ids = {
      gemini_api_key     = "mock-secret"
      openrouter_api_key = "mock-secret"
      langfuse_secret    = "mock-secret"
    }
  }
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//iam"
}

inputs = {
  service_accounts = include.env.locals.service_accounts
}
