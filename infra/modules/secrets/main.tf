resource "google_secret_manager_secret" "secret" {
  for_each = var.secrets

  project   = var.project_id
  secret_id = each.value.secret_id

  labels = merge(var.labels, {
    secret_name = each.key
  })

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "placeholder" {
  for_each = var.secrets

  secret      = google_secret_manager_secret.secret[each.key].id
  secret_data = "PLACEHOLDER_VALUE_REPLACE_ME"

  lifecycle {
    ignore_changes = [secret_data]
  }
}
