output "service_account_emails" {
  description = "Map of service account emails"
  value       = { for k, v in google_service_account.sa : k => v.email }
}

output "service_account_names" {
  description = "Map of service account names"
  value       = { for k, v in google_service_account.sa : k => v.name }
}

output "service_account_ids" {
  description = "Map of service account unique IDs"
  value       = { for k, v in google_service_account.sa : k => v.unique_id }
}
