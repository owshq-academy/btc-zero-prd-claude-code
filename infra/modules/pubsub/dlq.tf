resource "google_pubsub_topic" "dlq" {
  for_each = {
    for k, v in var.topics : k => v
    if v.enable_dlq
  }

  project = var.project_id
  name    = "${each.value.name}-dlq"

  message_retention_duration = each.value.message_retention_duration

  labels = merge(var.labels, {
    topic_name = "${each.key}-dlq"
    is_dlq     = "true"
  })
}

resource "google_pubsub_subscription" "dlq_subscription" {
  for_each = {
    for k, v in var.topics : k => v
    if v.enable_dlq
  }

  project = var.project_id
  name    = "${each.value.name}-dlq-sub"
  topic   = google_pubsub_topic.dlq[each.key].id

  ack_deadline_seconds       = 600
  message_retention_duration = "604800s"

  labels = merge(var.labels, {
    subscription_name = "${each.key}-dlq-sub"
    is_dlq            = "true"
  })
}
