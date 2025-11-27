# Terraform backend bootstrap

This folder provisions an S3 bucket and DynamoDB table used as Terraform
remote state backend and lock table. Run this only once (or when creating a
new environment).

Quickstart (PowerShell / with OIDC in CI):

```powershell
cd infra/terraform/bootstrap
terraform init
terraform plan -var="aws_region=us-east-1"
terraform apply -var="aws_region=us-east-1" -auto-approve
```

Notes
- The bucket and table names can be provided via `tf_state_bucket` and
  `tf_state_lock_table` variables to avoid random suffixes.
- In CI you should run this via a protected `workflow_dispatch` job that uses
  GitHub OIDC to assume an IAM role with permission to create S3 and DynamoDB resources.
