output "database_names" {
  description = "The names of the created Firestore databases"
  value = {
    primary   = google_firestore_database.primary_database.name
    secondary = google_firestore_database.secondary_database.name
  }
}

output "database_urls" {
  description = "The URLs of the Firestore databases"
  value = {
    primary   = "https://firestore.googleapis.com/v1/projects/${var.project_id}/databases/${google_firestore_database.primary_database.name}"
    secondary = "https://firestore.googleapis.com/v1/projects/${var.project_id}/databases/${google_firestore_database.secondary_database.name}"
  }
}

output "database_connection_strings" {
  description = "The connection strings for the Firestore databases"
  value = {
    primary   = "(default=${var.project_id}:${google_firestore_database.primary_database.name})"
    secondary = "(default=${var.project_id}:${google_firestore_database.secondary_database.name})"
  }
}

