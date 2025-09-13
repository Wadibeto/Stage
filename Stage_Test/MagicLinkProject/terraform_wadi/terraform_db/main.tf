provider "google" {
  project = var.project_id
  region  = "us-central1"
}

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

# Service Account pour Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "cloud-run-sa"
  display_name = "Cloud Run Service Account"
}

# Attribution des rôles nécessaires
resource "google_project_iam_member" "cloud_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Déploiement de Cloud Run avec du code source
resource "google_cloud_run_service" "flask" {
  name     = "flask-service"
  location = "us-central1"

  template {
    spec {
      service_account_name = google_service_account.cloud_run_sa.email

      containers {
        image = "gcr.io/google-appengine/python"  # Image de base de GCP pour Python
      }
    }
  }

  autogenerate_revision_name = true

  traffic {
    percent = 100
    latest_revision = true
  }
}

# Output de l'URL de Cloud Run
output "cloud_run_url" {
  description = "L'URL du service Cloud Run déployé"
  value       = google_cloud_run_service.flask.status[0].url
}
