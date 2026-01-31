output "bucket_names" {
  description = "Map of bucket names"
  value       = { for k, v in google_storage_bucket.bucket : k => v.name }
}

output "bucket_urls" {
  description = "Map of bucket URLs"
  value       = { for k, v in google_storage_bucket.bucket : k => v.url }
}

output "bucket_self_links" {
  description = "Map of bucket self links"
  value       = { for k, v in google_storage_bucket.bucket : k => v.self_link }
}
