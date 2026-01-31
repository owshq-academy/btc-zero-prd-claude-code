resource "google_pubsub_topic" "topic" {
  for_each = var.topics

  project = var.project_id
  name    = each.value.name

  message_retention_duration = each.value.message_retention_duration

  labels = merge(var.labels, {
    topic_name = each.key
  })
}

resource "google_pubsub_subscription" "subscription" {
  for_each = var.subscriptions

  project = var.project_id
  name    = each.value.name
  topic   = google_pubsub_topic.topic[each.value.topic_key].id

  ack_deadline_seconds = each.value.ack_deadline_seconds

  dynamic "push_config" {
    for_each = each.value.push_endpoint != null ? [1] : []
    content {
      push_endpoint = each.value.push_endpoint

      dynamic "oidc_token" {
        for_each = var.invoker_service_account != null ? [1] : []
        content {
          service_account_email = var.invoker_service_account
        }
      }
    }
  }

  retry_policy {
    minimum_backoff = each.value.min_retry_delay
    maximum_backoff = each.value.max_retry_delay
  }

  dynamic "dead_letter_policy" {
    for_each = var.topics[each.value.topic_key].enable_dlq ? [1] : []
    content {
      dead_letter_topic     = google_pubsub_topic.dlq[each.value.topic_key].id
      max_delivery_attempts = each.value.max_delivery_attempts
    }
  }

  labels = merge(var.labels, {
    subscription_name = each.key
  })
}
