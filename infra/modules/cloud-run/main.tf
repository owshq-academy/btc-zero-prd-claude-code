locals {
  service_name_map = {
    tiff_converter     = "tiff-to-png-converter"
    invoice_classifier = "invoice-classifier"
    data_extractor     = "data-extractor"
    bigquery_writer    = "bigquery-writer"
  }
}

resource "google_cloud_run_v2_service" "service" {
  for_each = var.services

  provider = google-beta
  project  = var.project_id
  location = var.region
  name     = "fnc-${lookup(local.service_name_map, each.key, each.key)}-${var.env == "prod" ? "prd" : var.env}"

  # Allow deletion for infrastructure management
  deletion_protection = false

  template {
    service_account = lookup(var.service_accounts, each.key, null)
    timeout         = "${each.value.timeout}s"

    scaling {
      min_instance_count = each.value.min_instances
      max_instance_count = each.value.max_instances
    }

    containers {
      image = var.use_placeholder_image ? var.placeholder_image : "gcr.io/${var.project_id}/${lookup(local.service_name_map, each.key, each.key)}:${var.image_tag}"

      resources {
        limits = {
          memory = each.value.memory
          cpu    = each.value.cpu
        }
      }

      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "ENVIRONMENT"
        value = var.env
      }

      dynamic "env" {
        for_each = var.gcs_buckets
        content {
          name  = "GCS_BUCKET_${upper(env.key)}"
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.pubsub_topics
        content {
          name  = "PUBSUB_TOPIC_${upper(env.key)}"
          value = env.value
        }
      }
    }

    max_instance_request_concurrency = each.value.concurrency
  }

  labels = merge(var.labels, {
    service_name = lookup(local.service_name_map, each.key, each.key)
    function     = each.key
  })

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }
}

resource "google_cloud_run_v2_service_iam_member" "pubsub_invoker" {
  for_each = var.invoker_service_account != null ? var.services : {}

  provider = google-beta
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.service[each.key].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.invoker_service_account}"
}
