# Terraform infra scaffold

This folder contains a minimal Terraform scaffold to provision AWS resources
for this demo project. It's intentionally small — use it as a starting point
and replace the example with production-grade modules (VPC, EKS module, IAM).

Quickstart (PowerShell)

```powershell
cd infra/terraform
terraform init
terraform plan -var="aws_region=us-east-1"
# Review plan. To apply (be careful - this creates cloud resources):
terraform apply -var="aws_region=us-east-1"
```

Notes
- This fileset is a scaffold; the recommended step is to adopt
  `terraform-aws-modules/eks/aws` and a VPC module and to manage state per
  environment (remote state backend).
- Set AWS credentials using environment variables or an AWS profile before
  running `terraform apply`.
