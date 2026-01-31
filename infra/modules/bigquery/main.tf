resource "google_bigquery_dataset" "dataset" {
  project    = var.project_id
  dataset_id = var.dataset_id
  location   = var.location

  description = var.description

  default_partition_expiration_ms = var.partition_expiration_days != null ? var.partition_expiration_days * 24 * 60 * 60 * 1000 : null

  labels = var.labels
}

resource "google_bigquery_table" "extractions" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = "extractions"

  time_partitioning {
    type  = "DAY"
    field = "processed_at"
  }

  clustering = ["vendor_type", "invoice_id"]

  schema = jsonencode([
    { name = "extraction_id", type = "STRING", mode = "REQUIRED" },
    { name = "invoice_id", type = "STRING", mode = "REQUIRED" },
    { name = "vendor_type", type = "STRING", mode = "REQUIRED" },
    { name = "restaurant_name", type = "STRING", mode = "NULLABLE" },
    { name = "restaurant_address", type = "STRING", mode = "NULLABLE" },
    { name = "order_id", type = "STRING", mode = "NULLABLE" },
    { name = "order_date", type = "DATE", mode = "NULLABLE" },
    { name = "subtotal", type = "NUMERIC", mode = "NULLABLE" },
    { name = "delivery_fee", type = "NUMERIC", mode = "NULLABLE" },
    { name = "service_fee", type = "NUMERIC", mode = "NULLABLE" },
    { name = "tip_amount", type = "NUMERIC", mode = "NULLABLE" },
    { name = "total_amount", type = "NUMERIC", mode = "NULLABLE" },
    { name = "currency", type = "STRING", mode = "NULLABLE" },
    { name = "source_file", type = "STRING", mode = "NULLABLE" },
    { name = "extraction_model", type = "STRING", mode = "NULLABLE" },
    { name = "extraction_latency_ms", type = "INT64", mode = "NULLABLE" },
    { name = "confidence_score", type = "FLOAT64", mode = "NULLABLE" },
    { name = "processed_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "metadata", type = "JSON", mode = "NULLABLE" }
  ])

  labels = merge(var.labels, {
    table_name = "extractions"
  })
}

resource "google_bigquery_table" "line_items" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = "line_items"

  time_partitioning {
    type  = "DAY"
    field = "processed_at"
  }

  clustering = ["invoice_id"]

  schema = jsonencode([
    { name = "line_item_id", type = "STRING", mode = "REQUIRED" },
    { name = "invoice_id", type = "STRING", mode = "REQUIRED" },
    { name = "description", type = "STRING", mode = "NULLABLE" },
    { name = "quantity", type = "INT64", mode = "NULLABLE" },
    { name = "unit_price", type = "NUMERIC", mode = "NULLABLE" },
    { name = "amount", type = "NUMERIC", mode = "NULLABLE" },
    { name = "processed_at", type = "TIMESTAMP", mode = "REQUIRED" }
  ])

  labels = merge(var.labels, {
    table_name = "line_items"
  })
}

resource "google_bigquery_table" "audit_log" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = "audit_log"

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["status", "function_name"]

  schema = jsonencode([
    { name = "log_id", type = "STRING", mode = "REQUIRED" },
    { name = "invoice_id", type = "STRING", mode = "NULLABLE" },
    { name = "function_name", type = "STRING", mode = "REQUIRED" },
    { name = "status", type = "STRING", mode = "REQUIRED" },
    { name = "message", type = "STRING", mode = "NULLABLE" },
    { name = "duration_ms", type = "INT64", mode = "NULLABLE" },
    { name = "timestamp", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "metadata", type = "JSON", mode = "NULLABLE" }
  ])

  labels = merge(var.labels, {
    table_name = "audit_log"
  })
}

resource "google_bigquery_table" "metrics" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = "metrics"

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["vendor_type", "extraction_model"]

  schema = jsonencode([
    { name = "metric_id", type = "STRING", mode = "REQUIRED" },
    { name = "vendor_type", type = "STRING", mode = "REQUIRED" },
    { name = "extraction_model", type = "STRING", mode = "REQUIRED" },
    { name = "total_invoices", type = "INT64", mode = "REQUIRED" },
    { name = "successful_extractions", type = "INT64", mode = "REQUIRED" },
    { name = "failed_extractions", type = "INT64", mode = "REQUIRED" },
    { name = "avg_latency_ms", type = "FLOAT64", mode = "NULLABLE" },
    { name = "avg_confidence_score", type = "FLOAT64", mode = "NULLABLE" },
    { name = "timestamp", type = "TIMESTAMP", mode = "REQUIRED" }
  ])

  labels = merge(var.labels, {
    table_name = "metrics"
  })
}
