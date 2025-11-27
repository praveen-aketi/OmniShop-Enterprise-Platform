variable "aws_region" {
  description = "AWS region for bootstrap resources"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS profile for local runs"
  type        = string
  default     = "default"
}

variable "cluster_name" {
  description = "Base name used for resources"
  type        = string
  default     = "devsecops-cluster"
}

variable "tf_state_bucket" {
  description = "Optional: pre-defined S3 bucket name for remote state"
  type        = string
  default     = ""
}

variable "tf_state_lock_table" {
  description = "Optional: pre-defined DynamoDB table name for state locking"
  type        = string
  default     = ""
}
