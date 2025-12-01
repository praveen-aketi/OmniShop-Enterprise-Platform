# OmniShop Enterprise Platform

**OmniShop** is a reference implementation of a modern, cloud-native enterprise e-commerce platform. It demonstrates a comprehensive DevSecOps approach for building secure, scalable, and automated microservices-based applications.

## 🚀 Project Overview

The platform consists of the following core business domains:
-   **Frontend Dashboard**: A modern React-based Single Page Application (SPA) for managing orders and products.
-   **Order Management System (OMS)**: Implemented as `orders-service`, handling customer order processing.
-   **Product Catalog Service (PCS)**: Implemented as `products-service`, managing inventory and product details.

Key capabilities demonstrated:
-   **Infrastructure as Code**: AWS infrastructure provisioning using Terraform (EKS, VPC, IAM).
-   **CI/CD**: Split GitHub Actions pipelines for optimized Application builds and Infrastructure deployment.
-   **GitOps**: Argo CD for continuous deployment to Kubernetes.
-   **Security**: Integrated security checks including SAST (SonarQube), Container Scanning (Trivy), and Image Signing (Cosign).
-   **Observability**: Scaffolding for Prometheus, Grafana, and ELK stack.

## 🛠️ Tech Stack

| Category | Tools |
|----------|-------|
| **Frontend** | React, Vite, CSS Modules |
| **Backend** | Python (Flask) |
| **Cloud Provider** | AWS |
| **Orchestration** | Kubernetes (EKS) |
| **IaC** | Terraform, Ansible |
| **CI/CD** | GitHub Actions, Argo CD |
| **Security** | SonarQube, Trivy, Cosign |
| **Artifacts** | Docker Hub |

## 📂 Repository Structure

```text
.
├── .github/workflows       # CI/CD Automation
│   ├── app-ci.yml          # CI: Build, Test, Scan & Push (Frontend + Backend)
│   └── infra-deploy.yml    # CD: Infrastructure Provisioning & GitOps Sync
├── frontend                # React Frontend Application
│   ├── src/components      # Reusable UI components (Dashboard, Sidebar, etc.)
│   └── public              # Static assets
├── infra                   # Infrastructure as Code (IaC)
│   ├── terraform           # AWS Provisioning (EKS, VPC, IAM, S3, DynamoDB)
│   ├── ansible             # Configuration Management (Optional)
│   └── iam                 # IAM Policies & Role Definitions
├── k8s                     # Kubernetes & GitOps Configuration
│   ├── argo                # ArgoCD ApplicationSets & Monitoring Stack
│   └── omnishop-chart      # Helm Chart for Microservices
│       ├── templates       # K8s Manifest Templates (Deployment, Service, Monitor)
│       └── values.yaml     # Default Configuration Values
├── orders-service          # Order Management Microservice (Python/Flask)
├── products-service        # Product Catalog Microservice (Python/Flask)
└── monitoring              # Observability Stack Configuration
    └── elk-stack           # Elasticsearch, Logstash, Kibana setup
```

## ⚡ Getting Started

### Prerequisites

-   [Docker](https://www.docker.com/)
-   [Node.js 18+](https://nodejs.org/)
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

2.  **Run Frontend Dashboard:**
    ```bash
    cd frontend
    npm install
    npm run dev
    # Access Dashboard: http://localhost:5173
    ```

3.  **Run Order Management Service (OMS):**
    ```bash
    cd orders-service
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python app.py
    # API: http://localhost:8080/api/orders
    ```

4.  **Run Product Catalog Service (PCS):**
    ```bash
    cd ../products-service
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python app.py
    # API: http://localhost:8081/api/products
    ```

## 🔄 CI/CD Pipelines

The project uses a split-pipeline architecture for efficiency:

### 1. Application CI (`app-ci.yml`)
Triggers on changes to `frontend/`, `orders-service/`, or `products-service/`.
-   **Build**: Docker builds for backend services, NPM build for frontend.
-   **Test**: Runs unit tests.
-   **Scan**: Trivy (Container Security) and SonarQube (Code Quality).
-   **Push**: Pushes signed images to Docker Hub.

### 2. Infrastructure Deploy (`infra-deploy.yml`)
Triggers on changes to `infra/` or `k8s/`.
-   **Terraform**: Plans and Applies AWS infrastructure changes.
-   **Argo CD**: Syncs Kubernetes manifests and updates the cluster.

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

