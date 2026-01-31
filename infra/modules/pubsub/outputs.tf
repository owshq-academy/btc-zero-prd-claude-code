output "topic_ids" {
  description = "Map of topic IDs"
  value       = { for k, v in google_pubsub_topic.topic : k => v.id }
}

output "topic_names" {
  description = "Map of topic names"
  value       = { for k, v in google_pubsub_topic.topic : k => v.name }
}

output "dlq_topic_ids" {
  description = "Map of DLQ topic IDs"
  value       = { for k, v in google_pubsub_topic.dlq : k => v.id }
}

output "subscription_ids" {
  description = "Map of subscription IDs"
  value       = { for k, v in google_pubsub_subscription.subscription : k => v.id }
}

output "subscription_names" {
  description = "Map of subscription names"
  value       = { for k, v in google_pubsub_subscription.subscription : k => v.name }
}
