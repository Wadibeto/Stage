terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = "votre-id-de-projet-gcp"
  region  = "us-central1"
}

resource "google_cloud_run_service" "magic_link_service" {
  name     = "magic-link-service"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/votre-id-de-projet-gcp/magic-link-app:latest"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Rendre le service public
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.magic_link_service.name
  location = google_cloud_run_service.magic_link_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "service_url" {
  value = google_cloud_run_service.magic_link_service.status[0].url
}

