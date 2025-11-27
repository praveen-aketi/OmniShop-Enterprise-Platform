# Interview: Project Use-Case Explanation

Overview
- This project demonstrates a cloud-native microservices platform built on AWS
  with Kubernetes. The key goals are reproducible infrastructure, opinionated
  CI/CD, and observability.

Architecture (high level)
- Infrastructure: AWS (VPC, EKS) provisioned via Terraform modules. The
  Terraform scaffold in `infra/terraform` is a starting point and should be
  replaced with production-quality modules and remote state.
- Compute: Kubernetes (EKS) hosts microservices `orders-service` and `products-service`.
- Delivery: Images are built in GitHub Actions and pushed to a container
  registry. Argo CD manages manifest synchronization from the repo to the
  cluster (see `k8s/argo/applicationset.yaml`).
- Observability: Prometheus scrapes metrics; Grafana dashboards visualize
  them; ELK (Elasticsearch/Kibana) aggregates logs. The manifests included are
  placeholders—use Helm charts for full installs.

CI/CD Flow
1. Developer pushes to `main` (or opens PR to feature branch).
2. GitHub Actions builds container images and pushes to a registry.
3. Terraform can provision or update infra (optional automated apply).
4. Argo CD (or `kubectl`) syncs `k8s/` manifests to the cluster.

Design Rationale
- GitOps: Argo CD ensures manifests in git are the single source of truth,
  enabling declarative drift detection and safe rollbacks.
- Terraform for infra: separation of concerns — infra (Terraform) vs runtime
  config (Kubernetes manifests).
- Monitoring & Logging: separated concerns for metrics (Prometheus) and logs
  (ELK) so teams can iterate independently.

Talking points for interviews
- Explain how you'd convert the scaffolds into production-ready stacks
  (remote state, IAM least privilege, CI secrets handling, multi-env). 
- Describe how you would secure the pipeline (signing images, OIDC for
  GitHub -> AWS, Argo CD RBAC, network policies for services).
- Explain strategies for multi-region/high-availability EKS clusters and
  how to test disaster recovery (DR) for stateful services.
