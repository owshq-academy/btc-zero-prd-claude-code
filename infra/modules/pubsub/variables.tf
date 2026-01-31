variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "topics" {
  description = "Map of Pub/Sub topics to create"
  type = map(object({
    name                       = string
    message_retention_duration = string
    enable_dlq                 = bool
  }))
}

variable "subscriptions" {
  description = "Map of subscriptions to create"
  type = map(object({
    topic_key             = string
    name                  = string
    push_endpoint         = optional(string)
    ack_deadline_seconds  = optional(number, 60)
    max_delivery_attempts = optional(number, 5)
    min_retry_delay       = optional(string, "10s")
    max_retry_delay       = optional(string, "600s")
  }))
  default = {}
}

variable "invoker_service_account" {
  description = "Service account email for Pub/Sub push invocation"
  type        = string
  default     = null
}

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default     = {}
}
