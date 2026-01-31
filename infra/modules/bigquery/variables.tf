variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
}

variable "location" {
  description = "Dataset location"
  type        = string
  default     = "US"
}

variable "description" {
  description = "Dataset description"
  type        = string
  default     = "Invoice extraction pipeline data"
}

variable "partition_expiration_days" {
  description = "Default partition expiration in days (null for no expiration)"
  type        = number
  default     = null
}

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default     = {}
}
