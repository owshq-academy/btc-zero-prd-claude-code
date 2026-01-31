variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "env" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "services" {
  description = "Map of Cloud Run services to deploy"
  type = map(object({
    memory        = string
    cpu           = string
    timeout       = number
    min_instances = number
    max_instances = number
    concurrency   = number
  }))
}

variable "service_accounts" {
  description = "Map of service account emails for each service"
  type        = map(string)
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

variable "use_placeholder_image" {
  description = "Use placeholder image for initial deployment (when actual images don't exist)"
  type        = bool
  default     = false
}

variable "placeholder_image" {
  description = "Placeholder image URL for initial deployment"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello:latest"
}

variable "env_vars" {
  description = "Environment variables for all services"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Map of secret IDs for services"
  type        = map(string)
  default     = {}
}

variable "pubsub_topics" {
  description = "Map of Pub/Sub topic IDs"
  type        = map(string)
  default     = {}
}

variable "gcs_buckets" {
  description = "Map of GCS bucket names"
  type        = map(string)
  default     = {}
}

variable "invoker_service_account" {
  description = "Service account for Pub/Sub push"
  type        = string
  default     = null
}

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default     = {}
}
