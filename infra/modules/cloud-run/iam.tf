resource "google_cloud_run_v2_service_iam_member" "noauth" {
  for_each = {
    for k, v in var.services : k => v
    if false
  }

  provider = google-beta
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.service[each.key].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
