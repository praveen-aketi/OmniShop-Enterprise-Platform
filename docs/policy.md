# CI / Security Policy (Guidance)

This document outlines recommended repository-level policies to enforce
security and release gates for this project.

Required checks (recommended)
- **CI/CD (Hardened)** workflow: require this workflow to pass on `main` before allowing merges.
- **SonarQube**: require Sonar quality gate to pass on PRs when configured with SonarCloud/self-hosted Sonar.
- **Trivy gating**: the pipeline already fails on HIGH/CRITICAL vulnerabilities — require the build status.
- **Cosign signature**: enable a manual check that verifies images are signed (cosign verify) as part of the release pipeline.

Branch protection setup
- Protect `main` with branch protection rules requiring:
  - At least one approving review (or more, per team policy)
  - Status checks: `CI/CD (Hardened)` and any other required checks (Sonar, Trivy)
  - Dismiss stale reviews when new commits are pushed

Enforcement options
- Use GitHub Actions checks and branch protection to prevent merges.
- For runtime admission control enforce image signature verification via an admission controller (e.g., Kyverno or OPA Gatekeeper) that denies unsigned images.

Operations
- To create the remote state bucket and lock table use the `Bootstrap Terraform Backend` workflow (requires `AWS_ROLE_TO_ASSUME` and OIDC setup). This should be run once and then the CI `CI/CD (Hardened)` workflow will use the backend via `TF_STATE_BUCKET` and `TF_STATE_LOCK_TABLE` secrets.
