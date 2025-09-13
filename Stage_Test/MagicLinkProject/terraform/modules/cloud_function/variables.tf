variable "project_id" {
  description = "The ID of the project in which resources will be managed."
  type        = string
}

variable "region" {
  description = "The region in which resources will be managed."
  type        = string
}

variable "function_name" {
  description = "The name of the Cloud Function."
  type        = string
  default     = "default-function"
}

variable "function_description" {
  description = "The description of the Cloud Function."
  type        = string
  default     = "Default function description"
}

variable "runtime" {
  description = "The runtime in which the function will be executed."
  type        = string
  default     = "python39"
}

variable "entry_point" {
  description = "The entry point of the function."
  type        = string
  default     = "default_entry_point"
}

variable "source_dir" {
  description = "The directory containing the function source code."
  type        = string
  default     = "./function_files/default"
}

variable "auth0_client_id" {
  description = "The Client ID for Auth0 authentication."
  type        = string
}

variable "auth0_client_secret" {
  description = "The Client Secret for Auth0 authentication."
  type        = string
}

variable "auth0_domain" {
  description = "The Auth0 domain."
  type        = string
}

variable "auth0_audience" {
  description = "The Auth0 API audience."
  type        = string
}
