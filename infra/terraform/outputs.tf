output "kubeconfig_command" {
  description = "Command to obtain kubeconfig for the cluster"
  value       = "aws eks --region ${var.aws_region} update-kubeconfig --name ${module.eks.cluster_id}"
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_ca" {
  value = module.eks.cluster_certificate_authority_data
}
