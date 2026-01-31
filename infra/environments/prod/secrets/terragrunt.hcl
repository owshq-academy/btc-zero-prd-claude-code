include "root" {
  path = find_in_parent_folders()
}

include "env" {
  path   = find_in_parent_folders("env.hcl")
  expose = true
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules//secrets"
}

inputs = {
  secrets = include.env.locals.secrets_config
}
