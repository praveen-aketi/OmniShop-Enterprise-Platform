variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS CLI profile name to use for local runs"
  type        = string
  default     = "default"
}

variable "cluster_name" {
  description = "EKS cluster name (scaffold)"
  type        = string
  default     = "devsecops-cluster"
}

variable "node_group_desired_capacity" {
  description = "Desired node group size"
  type        = number
  default     = 2
}

variable "node_group_max_capacity" {
  description = "Max node group size"
  type        = number
  default     = 3
}

variable "tf_state_bucket" {
  description = "S3 bucket name to store Terraform remote state"
  type        = string
  default     = "" # set in CI or override when running
}

variable "tf_state_lock_table" {
  description = "DynamoDB table name to use for Terraform state locking"
  type        = string
  default     = "" # set in CI or override when running
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "List of public subnet cidrs"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "List of private subnet cidrs"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

