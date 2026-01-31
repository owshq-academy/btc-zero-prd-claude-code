variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "service_accounts" {
  description = "Map of service accounts to create"
  type = map(object({
    account_id   = string
    display_name = string
    roles        = list(string)
  }))
}
