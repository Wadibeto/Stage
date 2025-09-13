output "function_urls" {
  value       = module.cloud_functions.function_urls
  description = "The URLs of the deployed Cloud Functions"
}

output "function_names" {
  value       = module.cloud_functions.function_names
  description = "The names of the deployed Cloud Functions"
}

output "enabled_apis" {
  value       = module.api_enablement.enabled_apis
  description = "List of enabled APIs"
}

output "firestore_database_names" {
  value       = module.storage.database_names
  description = "Names of the Firestore databases"
}

output "firestore_database_urls" {
  value       = module.storage.database_urls
  description = "URLs of the Firestore databases"
}

output "firestore_connection_strings" {
  value       = module.storage.database_connection_strings
  description = "Connection strings for the Firestore databases"
}

