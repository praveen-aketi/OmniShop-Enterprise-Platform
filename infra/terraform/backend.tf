/*
  Remote state backend configuration. Replace `bucket` and `dynamodb_table`
  by passing `-var "tf_state_bucket=<bucket>" -var "tf_state_lock_table=<table>"`
  or set them in a `terraform.tfvars` file (do NOT commit credentials).
*/

terraform {
# backend "s3" {
  #   key     = "devsecops/terraform.tfstate"
  #   encrypt = true
  #   # bucket, region, and dynamodb_table will be passed via -backend-config
  # }
}
