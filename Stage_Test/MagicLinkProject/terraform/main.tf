// File: MagicLinkProject/terraform/main.tf
provider "google" {
  project     = var.project_id
  region      = var.region
  credentials = file("terraform-sa-key.json")
}

module "api_enablement" {
  source        = "./modules/api_enablement"
  project_id    = var.project_id
  apis_to_enable = [
    "cloudfunctions.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "firestore.googleapis.com"
  ]
}

module "storage" {
  source     = "./modules/storage"
  project_id = var.project_id
  region     = var.region
}

module "cloud_functions" {
  source     = "./modules/cloud_function"
  project_id = var.project_id
  region     = var.region
  depends_on = [module.api_enablement]
  
  function_name        = "default-function"
  function_description = "Default function description"
  runtime              = "python39"
  entry_point          = "default_entry_point"
  source_dir           = "./modules/cloud_function/function_files/default"

  auth0_domain        = var.auth0_domain
  auth0_client_id     = var.auth0_client_id
  auth0_client_secret = var.auth0_client_secret
  auth0_audience      = var.auth0_audience
}