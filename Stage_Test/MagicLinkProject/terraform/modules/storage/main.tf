resource "google_firestore_database" "primary_database" {
  project     = var.project_id
  name        = "primary-database"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

resource "google_firestore_database" "secondary_database" {
  project     = var.project_id
  name        = "secondary-database"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# IAM configuration for Firestore
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${var.project_id}@appspot.gserviceaccount.com"
}
