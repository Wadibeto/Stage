locals {
  functions = [
    {
      name        = "ai-exchange"
      description = "AI Exchange Function"
      entry_point = "ai_exchange"
      source_dir  = "${path.module}/function_files/ai_exchange"
    },
    {
      name        = "ping-check"
      description = "Ping Check Function"
      entry_point = "ping_check"
      source_dir  = "${path.module}/function_files/ping_check"
    },
    {
      name        = "gemini-exchange"
      description = "Gemini Exchange Function"
      entry_point = "gemini_exchange"
      source_dir  = "${path.module}/function_files/gemini_exchange"
    },
    {
      name        = "gemini_complicated"
      description = "Gemini Complicated Function"
      entry_point = "gemini_complicated"
      source_dir  = "${path.module}/function_files/gemini_complicated"
    },
    {
      name        = "storage_data_management"
      description = "Storage Data Management Function"
      entry_point = "storage_data_management"
      source_dir  = "${path.module}/function_files/storage_data_management"
    },
    {
      name        = "perplexity_sonar"
      description = "Perplexity Sonar Function"
      entry_point = "perplexity_sonar"
      source_dir  = "${path.module}/function_files/perplexity_sonar"
    },
    {
      name        = "auth0_function"
      description = "Auth0 Authentication Function"
      entry_point = "auth0_function"
      source_dir  = "${path.module}/function_files/auth0_function"
    }
  ]
}

resource "google_storage_bucket" "function_bucket" {
  name     = "${var.project_id}-functions-source"
  location = var.region
}

data "archive_file" "function_zip" {
  for_each = { for f in local.functions : f.name => f }

  type        = "zip"
  source_dir  = each.value.source_dir
  output_path = "/tmp/${each.value.name}.zip"
}

resource "google_storage_bucket_object" "function_zip" {
  for_each = { for f in local.functions : f.name => f }
  depends_on = [google_storage_bucket.function_bucket]

  name   = "${each.value.name}-${data.archive_file.function_zip[each.key].output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = data.archive_file.function_zip[each.key].output_path
}

resource "google_cloudfunctions_function" "function" {
  for_each = { for f in local.functions : f.name => f }

  name        = each.value.name
  description = each.value.description
  runtime     = "python39"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.function_zip[each.key].name
  trigger_http          = true
  entry_point           = each.value.entry_point

  # Ajout des variables d'environnement pour Auth0
  environment_variables = (
    each.value.name == "auth0_function" ? {
      AUTH0_CLIENT_ID     = var.auth0_client_id
      AUTH0_CLIENT_SECRET = var.auth0_client_secret
      AUTH0_DOMAIN        = var.auth0_domain
      AUTH0_AUDIENCE      = var.auth0_audience
    } : {}
  )
}


resource "google_cloudfunctions_function_iam_member" "invoker" {
  for_each = { for f in local.functions : f.name => f }

  project        = google_cloudfunctions_function.function[each.key].project
  region         = google_cloudfunctions_function.function[each.key].region
  cloud_function = google_cloudfunctions_function.function[each.key].name

  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}

