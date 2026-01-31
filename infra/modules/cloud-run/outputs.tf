output "service_urls" {
  description = "Map of Cloud Run service URLs"
  value       = { for k, v in google_cloud_run_v2_service.service : k => v.uri }
}

output "service_names" {
  description = "Map of Cloud Run service names"
  value       = { for k, v in google_cloud_run_v2_service.service : k => v.name }
}

output "service_ids" {
  description = "Map of Cloud Run service IDs"
  value       = { for k, v in google_cloud_run_v2_service.service : k => v.id }
}

output "service_locations" {
  description = "Map of Cloud Run service locations"
  value       = { for k, v in google_cloud_run_v2_service.service : k => v.location }
}
