resource "google_storage_bucket" "bucket" {
  for_each = var.buckets

  project       = var.project_id
  name          = each.value.name
  location      = each.value.location
  storage_class = each.value.storage_class

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  dynamic "lifecycle_rule" {
    for_each = each.value.lifecycle_age_days != null ? [1] : []
    content {
      condition {
        age = each.value.lifecycle_age_days
      }
      action {
        type = "Delete"
      }
    }
  }

  labels = merge(var.labels, {
    bucket_purpose = each.key
  })
}

resource "google_storage_notification" "notification" {
  for_each = {
    for k, v in var.buckets : k => v
    if v.enable_notification && var.notification_topic_id != null
  }

  bucket         = google_storage_bucket.bucket[each.key].name
  payload_format = "JSON_API_V1"
  topic          = var.notification_topic_id
  event_types    = ["OBJECT_FINALIZE"]

  custom_attributes = {
    bucket_name = each.value.name
  }

  object_name_prefix = each.value.notification_prefix

  depends_on = [google_storage_bucket.bucket]
}
