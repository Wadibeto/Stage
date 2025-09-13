# Provider configuration
provider "google" {
  credentials = file("terraform-key.json")
  project     = "omega-wind-448707-r4"
  region      = "europe-west6"
}

# Ajoutez cette ressource avant les Cloud Functions
resource "google_app_engine_application" "app" {
  project     = "omega-wind-448707-r4"
  location_id = "europe-west6"
  database_type = "CLOUD_FIRESTORE"

  lifecycle {
    prevent_destroy = true
  }
}

# Firestore database
resource "google_firestore_database" "database" {
  project     = "omega-wind-448707-r4"
  name        = "(default)"
  location_id = "europe-west6"
  type        = "FIRESTORE_NATIVE"

  lifecycle {
    prevent_destroy = true
  }
}

# Bucket pour stocker le code source des fonctions
resource "google_storage_bucket" "function_bucket" {
  name     = "omega-wind-448707-r4-functions"
  location = "europe-west6"
}

# Enable Cloud Functions API
resource "google_project_service" "cloudfunctions" {
  project = "omega-wind-448707-r4"
  service = "cloudfunctions.googleapis.com"
  disable_dependent_services = true
}

# Enable Firestore API
resource "google_project_service" "firestore" {
  project = "omega-wind-448707-r4"
  service = "firestore.googleapis.com"

  disable_dependent_services = true
}

# Enable App Engine API
resource "google_project_service" "appengine" {
  project = "omega-wind-448707-r4"
  service = "appengine.googleapis.com"
  disable_dependent_services = true
}

# Upload du code source pour la fonction 1
resource "google_storage_bucket_object" "function_1_source" {
  name   = "function_1_source_${filemd5("function_1_source.zip")}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = "function_1_source.zip"
}

# Upload du code source pour la fonction 2
resource "google_storage_bucket_object" "function_2_source" {
  name   = "function_2_source_${filemd5("function_2_source.zip")}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = "function_2_source.zip"
}

# Fonction Cloud 1
resource "google_cloudfunctions_function" "function_1" {
  name        = "convert-csv-to-json"
  description = "Convertit un CSV en JSON et enregistre les logs"
  runtime     = "python310"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.function_1_source.name
  trigger_http          = true
  entry_point           = "function_1_handler"
}

# Fonction Cloud 2
resource "google_cloudfunctions_function" "function_2" {
  name        = "get-logs"
  description = "R├®cup├¿re les logs des conversions"
  runtime     = "python310"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.function_2_source.name
  trigger_http          = true
  entry_point           = "function_2_handler"
}

# IAM for function 1
resource "google_cloudfunctions_function_iam_member" "invoker_1" {
  project        = google_cloudfunctions_function.function_1.project
  region         = google_cloudfunctions_function.function_1.region
  cloud_function = google_cloudfunctions_function.function_1.name

  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}

# IAM for function 2
resource "google_cloudfunctions_function_iam_member" "invoker_2" {
  project        = google_cloudfunctions_function.function_2.project
  region         = google_cloudfunctions_function.function_2.region
  cloud_function = google_cloudfunctions_function.function_2.name

  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}