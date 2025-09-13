output "function_urls" {
  value = {
    for name, function in google_cloudfunctions_function.function :
    name => function.https_trigger_url
  }
  description = "The URLs of the deployed Cloud Functions"
}

output "function_names" {
  value = {
    for name, function in google_cloudfunctions_function.function :
    name => function.name
  }
  description = "The names of the deployed Cloud Functions"
}
