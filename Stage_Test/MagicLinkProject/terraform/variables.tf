// File: MagicLinkProject/terraform/variables.tf
variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  description = "The region in which resources will be managed."
  default     = "europe-west1"
}

variable "auth0_domain" {
  type        = string
  description = "Auth0 Domain"
}

variable "auth0_client_id" {
  type        = string
  description = "Auth0 Client ID"
}

variable "auth0_client_secret" {
  type        = string
  description = "Auth0 Client Secret"
}

variable "auth0_audience" {
  type        = string
  description = "Auth0 API Audience"
}
