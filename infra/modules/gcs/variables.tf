variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "buckets" {
  description = "Map of buckets to create"
  type = map(object({
    name                = string
    location            = string
    storage_class       = string
    lifecycle_age_days  = optional(number)
    enable_notification = bool
    notification_prefix = optional(string)
  }))
}

variable "notification_topic_id" {
  description = "Pub/Sub topic ID for GCS notifications"
  type        = string
  default     = null
}

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default     = {}
}
