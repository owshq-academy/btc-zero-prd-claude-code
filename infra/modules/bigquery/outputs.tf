output "dataset_id" {
  description = "Dataset ID"
  value       = google_bigquery_dataset.dataset.dataset_id
}

output "dataset_self_link" {
  description = "Dataset self link"
  value       = google_bigquery_dataset.dataset.self_link
}

output "table_ids" {
  description = "Map of table IDs"
  value = {
    extractions = google_bigquery_table.extractions.table_id
    line_items  = google_bigquery_table.line_items.table_id
    audit_log   = google_bigquery_table.audit_log.table_id
    metrics     = google_bigquery_table.metrics.table_id
  }
}

output "table_full_ids" {
  description = "Map of full table IDs (project:dataset.table)"
  value = {
    extractions = "${var.project_id}:${google_bigquery_dataset.dataset.dataset_id}.${google_bigquery_table.extractions.table_id}"
    line_items  = "${var.project_id}:${google_bigquery_dataset.dataset.dataset_id}.${google_bigquery_table.line_items.table_id}"
    audit_log   = "${var.project_id}:${google_bigquery_dataset.dataset.dataset_id}.${google_bigquery_table.audit_log.table_id}"
    metrics     = "${var.project_id}:${google_bigquery_dataset.dataset.dataset_id}.${google_bigquery_table.metrics.table_id}"
  }
}
