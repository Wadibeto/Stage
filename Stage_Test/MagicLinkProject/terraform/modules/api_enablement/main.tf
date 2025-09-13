resource "google_project_service" "apis" {
  for_each = toset(var.apis_to_enable)
  project  = var.project_id
  service  = each.value

  disable_dependent_services = true
  disable_on_destroy         = false
}
