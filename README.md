# OmniShop Enterprise Platform

**OmniShop** is a reference implementation of a modern, cloud-native enterprise e-commerce platform. It demonstrates a comprehensive DevSecOps approach for building secure, scalable, and automated microservices-based applications.

## 🚀 Project Overview

The platform consists of the following core business domains:
-   **Order Management System (OMS)**: Implemented as `orders-service`, handling customer order processing.
-   **Product Catalog Service (PCS)**: Implemented as `products-service`, managing inventory and product details.

Key capabilities demonstrated:
-   **Infrastructure as Code**: AWS infrastructure provisioning using Terraform (EKS, VPC, IAM).
-   **CI/CD**: GitHub Actions pipelines for building, testing, security scanning, and deploying.
-   **GitOps**: Argo CD for continuous deployment to Kubernetes.
-   **Security**: Integrated security checks including SAST (SonarQube), Container Scanning (Trivy), and Image Signing (Cosign).
-   **Observability**: Scaffolding for Prometheus, Grafana, and ELK stack.

## 🛠️ Tech Stack

| Category | Tools |
|----------|-------|
| **Cloud Provider** | AWS |
| **Orchestration** | Kubernetes (EKS) |
| **IaC** | Terraform, Ansible |
| **CI/CD** | GitHub Actions, Argo CD |
| **Languages** | Python, HCL, YAML, Bash |
| **Security** | SonarQube, Trivy, Cosign |
| **Artifacts** | Docker Hub |

## 📂 Repository Structure

```text
.
├── .github/workflows   # CI/CD pipelines (Build, Scan, Deploy)
├── infra               # Infrastructure as Code
│   ├── terraform       # AWS infrastructure (EKS, VPC, etc.)
│   ├── ansible         # Configuration management
│   └── iam             # IAM policies and roles
├── k8s                 # Kubernetes manifests
│   ├── argo            # Argo CD ApplicationSets and configurations
│   ├── orders-service  # Order Management System manifests
│   └── products-service# Product Catalog Service manifests
├── orders-service      # Python microservice (OMS)
├── products-service    # Python microservice (PCS)
└── monitoring          # Observability configurations
```

## ⚡ Getting Started

### Prerequisites

-   [Docker](https://www.docker.com/)
-   [Python 3.9+](https://www.python.org/)
-   [Terraform](https://www.terraform.io/)
-   [kubectl](https://kubernetes.io/docs/tasks/tools/)
-   [AWS CLI](https://aws.amazon.com/cli/)

### Local Development

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/OmniShop-Platform.git
    cd OmniShop-Platform
    ```

2.  **Run Order Management Service (OMS):**
    ```bash
    cd orders-service
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python app.py
    # Health check: http://localhost:8080/health
    ```

3.  **Run Product Catalog Service (PCS):**
    ```bash
    cd ../products-service
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python app.py
    # Health check: http://localhost:8081/health
    ```

4.  **Run Tests:**
    Each service includes a `tests/` directory with `pytest` unit tests.
    ```bash
    # From orders-service or products-service directory
    pip install pytest
    pytest
    ```

## 📊 Monitoring & Observability

The project includes a comprehensive monitoring stack:

### Prometheus & Grafana (Metrics)
-   **Stack**: Deployed using the `kube-prometheus-stack` Helm chart via ArgoCD.
-   **Components**: Prometheus, Grafana, Alertmanager, Node Exporter.
-   **Service Monitoring**: Both `orders-service` and `products-service` are instrumented with `prometheus-flask-exporter` and have dedicated `ServiceMonitor` resources.
-   **Access**: Grafana is exposed via a LoadBalancer service. Default admin password is `admin`.

### ELK Stack (Logs)
-   **Elasticsearch**: A single-node deployment is defined in `monitoring/elk-stack/elastic-deployment.yaml`.
-   **Production Note**: For production environments, it is highly recommended to use the official [Elastic Helm Charts](https://github.com/elastic/helm-charts) for better scalability and management.

## 🔄 CI/CD Pipeline

The pipeline defined in `.github/workflows/ci-cd.yml` performs the following steps:

1.  **Checkout**: Fetches the code.
2.  **Build**: Docker builds for `orders-service` and `products-service`.
3.  **Push**: Pushes images to Docker Hub.
4.  **Sign**: Signs the container images using **Cosign** (Keyless or KMS).
5.  **Scan**:
    -   **Trivy**: Scans images for Critical/High vulnerabilities.
    -   **SonarQube**: Performs static code analysis.
6.  **Deploy**:
    -   **Terraform**: Provisions/Updates AWS infrastructure.
    -   **Argo CD**: Syncs the state of the cluster with the `k8s/` directory.

## 🔐 Security & Configuration

### Account Setup & Secrets Configuration

To successfully run the CI/CD pipeline, you need to configure the following accounts and add their credentials as **GitHub Repository Secrets**.

#### 1. AWS Account (Infrastructure)
Used to host the Kubernetes cluster (EKS) and store Terraform state.
-   **Prerequisites**:
    -   Create an S3 Bucket for Terraform state (e.g., `omnishop-tf-state`).
    -   Create a DynamoDB Table for state locking (e.g., `omnishop-tf-lock`, Partition key: `LockID`).
    -   Create an IAM Role with OIDC trust for GitHub Actions.

#### 2. Docker Hub (Artifacts)
Used to store container images.
-   **Sign up**: [hub.docker.com](https://hub.docker.com/)

#### 3. SonarCloud (Code Quality)
Used for static code analysis.
-   **Sign up**: [sonarcloud.io](https://sonarcloud.io/)
-   **Setup**: Create an Organization and Project, then generate a Security Token.

#### Required GitHub Secrets
Go to **Settings** -> **Secrets and variables** -> **Actions** in your repository and add:

| Secret Name | Description | Example Value |
| :--- | :--- | :--- |
| `AWS_REGION` | AWS Region for deployment | `us-east-1` |
| `AWS_ROLE_TO_ASSUME` | IAM Role ARN for GitHub Actions | `arn:aws:iam::123456789012:role/GitHubActionRole` |
| `TF_STATE_BUCKET` | S3 Bucket for Terraform state | `omnishop-tf-state` |
| `TF_STATE_LOCK_TABLE` | DynamoDB Table for locking | `omnishop-tf-lock` |
| `DOCKER_USERNAME` | Docker Hub Username | `jdoe` |
| `DOCKER_PASSWORD` | Docker Hub Password/Token | `dckr_pat_...` |
| `SONAR_ORG` | SonarCloud Organization Key | `my-org` |
| `SONAR_HOST_URL` | SonarCloud URL | `https://sonarcloud.io` |
| `SONAR_TOKEN` | SonarCloud Security Token | `abc123...` |
| `COSIGN_KEY_ARN` | (Optional) AWS KMS Key ARN for signing | `arn:aws:kms:...` |

### Infrastructure
See `infra/terraform/README.md` for detailed instructions on provisioning the AWS environment.
The Terraform scaffold includes:
-   `main.tf`: Main configuration.
-   `backend.tf`: Remote state configuration (S3 + DynamoDB).
-   `variables.tf`: Input variables.

To run Terraform locally:
```powershell
cd infra/terraform
terraform init
terraform plan -var="aws_region=us-east-1"
terraform apply -var="aws_region=us-east-1"
```

### 💣 Destroying the Infrastructure

To tear down the environment and avoid incurring costs, follow these steps:

1.  **Delete Kubernetes Load Balancers (Important)**:
    Terraform may not be able to delete the VPC if Load Balancers created by Kubernetes services still exist.
    ```bash
    # List Load Balancers
    aws elb describe-load-balancers --region us-east-1
    
    # Delete Load Balancer (replace with your LB name)
    aws elb delete-load-balancer --load-balancer-name <your-lb-name> --region us-east-1
    ```

2.  **Run Terraform Destroy**:
    ```bash
    cd infra/terraform
    terraform destroy -auto-approve -var="aws_region=us-east-1"
    ```
    *Note: If destroy fails due to dependencies (like Security Groups), ensure all Load Balancers and their Security Groups are deleted first.*

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---
*Note: This project is for educational and demonstration purposes.*

