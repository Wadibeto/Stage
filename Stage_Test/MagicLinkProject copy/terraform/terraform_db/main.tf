provider "google" {
  project = "eternal-sylph-449610-r3"
  region  = "us-central1"
}

resource "google_firestore_database" "default" {
  name        = "(default)"
  location_id = "europe-west2"
  type        = "FIRESTORE_NATIVE"
}
