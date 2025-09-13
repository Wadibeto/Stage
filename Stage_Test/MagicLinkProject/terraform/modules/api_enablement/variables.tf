variable "project_id" {
  description = "The ID of the project in which to enable APIs"
  type        = string
}

variable "apis_to_enable" {
  description = "List of APIs to enable in the project"
  type        = list(string)
}
