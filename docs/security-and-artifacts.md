# Security Scanning and Artifact Management

This document lists how the repository integrates security scanning and
artifact management tools used in the project.

Trivy (Container Scanning)
- We use `aquasecurity/trivy-action` in the GitHub Actions workflow to scan
  container images. The CI workflow scans both base images and built images.
- Required secrets:
  - `DOCKER_USERNAME`, `DOCKER_PASSWORD`

Gating and signing
- Trivy is configured to fail the build if `HIGH` or `CRITICAL` vulnerabilities
  are found in built images (see CI workflow). Adjust severity or add SBOM
  reporting as needed.
- Images are signed in CI using `cosign` (keyless signing). The workflow runs
  `cosign sign --keyless <image>` which uses OIDC to obtain a short-lived
  identity and write signatures to the transparency log. For stricter policies
  you can configure cosign with a KMS-backed key and restrict signing to
  specific runners/service accounts.

SonarQube / SonarCloud (Code Quality)
- A Sonar scanner step is included in the CI workflow. It expects:
  - `SONAR_TOKEN` and `SONAR_HOST_URL` (for self-hosted SonarQube) or use
    SonarCloud environment variables if using SonarCloud.
- `sonar-project.properties` in the repo root configures basic project
  metadata used by the scanner.

Docker Hub (Artifact Registry)
- Docker images are pushed to Docker Hub. In the workflow set these secrets on
  the repo: `DOCKER_USERNAME`, `DOCKER_PASSWORD`.
- Use repository paths like: `${DOCKER_USERNAME}/image:tag`

Notes on security
- Prefer GitHub OIDC for short-lived AWS credentials instead of storing long
  lived AWS keys in secrets when using Terraform. The workflow currently
  references `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` for apply steps.
- For production scanning consider adding:
  - SBOM generation
  - Vulnerability gating (fail the job for high/critical vulnerabilities)
  - Image signing (cosign)

Terraform remote state & OIDC
- The CI workflow uses OIDC to assume an AWS role for Terraform operations.
  Create an IAM role with a trusted identity provider for GitHub Actions and
  limit its permissions to the resources the pipeline must manage (least
  privilege). Set the repo secret `AWS_ROLE_TO_ASSUME` to the role ARN.

