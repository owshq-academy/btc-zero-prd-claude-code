output "secret_ids" {
  description = "Map of secret IDs"
  value       = { for k, v in google_secret_manager_secret.secret : k => v.secret_id }
}

output "secret_names" {
  description = "Map of secret resource names"
  value       = { for k, v in google_secret_manager_secret.secret : k => v.name }
}

output "secret_versions" {
  description = "Map of latest secret versions"
  value       = { for k, v in google_secret_manager_secret_version.placeholder : k => v.version }
}
