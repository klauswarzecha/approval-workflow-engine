variable "aws_region" {
  type        = string
  description = "AWS region for all resources."
  default     = "eu-central-1"
}

variable "project_name" {
  type        = string
  description = "Project name used for naming."
  default     = "approval-workflow-engine"
}

variable "tags" {
  type        = map(string)
  description = "Tags alpplied to all resources via provider default_tags."
  default = {
    Project     = "approval-workflow-engine"
    ManagedBy   = "opentofu"
  }
}