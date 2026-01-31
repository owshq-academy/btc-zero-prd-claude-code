locals {
  env_config = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  project_id = local.env_config.locals.project_id
  region     = local.env_config.locals.region
  env        = local.env_config.locals.environment
}

generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  backend "gcs" {
    bucket = "${local.project_id}-tfstate"
    prefix = "${path_relative_to_include()}"
  }
}
EOF
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "google" {
  project = "${local.project_id}"
  region  = "${local.region}"
}

provider "google-beta" {
  project = "${local.project_id}"
  region  = "${local.region}"
}
EOF
}

inputs = {
  project_id = local.project_id
  region     = local.region
  env        = local.env

  labels = {
    environment = local.env
    project     = "invoice-pipeline"
    managed_by  = "terragrunt"
  }
}
