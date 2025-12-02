# OmniShop Enterprise Platform 🚀

**OmniShop** is a complete, production-ready DevSecOps reference implementation showcasing modern cloud-native e-commerce architecture. This project demonstrates end-to-end automation, security best practices, and enterprise-grade observability.

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Tech Stack](#️-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start Guide](#-quick-start-guide)
- [Deployment Guide](#-deployment-guide)
- [Accessing Your Services](#-accessing-your-services)
- [Monitoring & Observability](#-monitoring--observability)
- [CI/CD Pipelines](#-cicd-pipelines)
- [Security](#-security)
- [Troubleshooting](#-troubleshooting)
- [Cleanup](#-cleanup)

---

## 🎯 Overview

OmniShop is a microservices-based e-commerce platform consisting of:

- **Frontend Dashboard**: React-based SPA for managing orders and products
- **Orders Service**: RESTful API for order management (Python/Flask)
- **Products Service**: RESTful API for product catalog (Python/Flask)
- **Monitoring Stack**: Prometheus + Grafana for metrics and dashboards
- **GitOps**: ArgoCD for continuous deployment

### Key Features

✅ **Infrastructure as Code** - Complete AWS infrastructure via Terraform  
✅ **Automated CI/CD** - GitHub Actions pipelines for build, test, and deploy  
✅ **GitOps** - ArgoCD for declarative Kubernetes deployments  
✅ **Security Scanning** - Trivy for container scanning, Cosign for image signing  
✅ **Observability** - Prometheus metrics, Grafana dashboards  
✅ **Multi-Environment** - Dev, Stage, and Prod environments

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AWS Cloud (EKS)                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   Kubernetes Cluster                  │  │
│  │                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │  │
│  │  │ Frontend │  │  Orders  │  │ Products │           │  │
│  │  │   (React)│  │ Service  │  │ Service  │           │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘           │  │
│  │       │             │             │                  │  │
│  │       └─────────────┴─────────────┘                  │  │
│  │                     │                                │  │
│  │       ┌─────────────┴─────────────┐                  │  │
│  │       │                           │                  │  │
│  │  ┌────▼─────┐              ┌──────▼──────┐          │  │
│  │  │ Prometheus│              │   Grafana   │          │  │
│  │  │  Metrics  │              │ Dashboards  │          │  │
│  │  └───────────┘              └─────────────┘          │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────┐     │  │
│  │  │            ArgoCD (GitOps)                  │     │  │
│  │  └─────────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Frontend** | React 18, Vite, Axios |
| **Backend** | Python 3.9+, Flask |
| **Cloud** | AWS (EKS, VPC, IAM, S3, DynamoDB) |
| **Container** | Docker, Kubernetes |
| **IaC** | Terraform |
| **CI/CD** | GitHub Actions, ArgoCD |
| **Monitoring** | Prometheus, Grafana |
| **Security** | Trivy, Cosign |
| **Registry** | Docker Hub |

---

## 📦 Prerequisites

Before you begin, ensure you have:

### Required Accounts

1. **AWS Account** - [Sign up here](https://aws.amazon.com/)
2. **GitHub Account** - [Sign up here](https://github.com/)
3. **Docker Hub Account** - [Sign up here](https://hub.docker.com/)

### Required Tools

Install the following tools on your local machine:

```bash
# Check if tools are installed
docker --version          # Docker 20.10+
node --version           # Node.js 18+
python --version         # Python 3.9+
terraform --version      # Terraform 1.0+
kubectl version --client # kubectl 1.24+
aws --version           # AWS CLI 2.0+
```

**Installation Links:**
- [Docker](https://docs.docker.com/get-docker/)
- [Node.js](https://nodejs.org/)
- [Python](https://www.python.org/downloads/)
- [Terraform](https://developer.hashicorp.com/terraform/downloads)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [AWS CLI](https://aws.amazon.com/cli/)

---

## 🚀 Quick Start Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/praveen-aketi/OmniShop-Enterprise-Platform.git
cd OmniShop-Enterprise-Platform
```

### Step 2: Configure AWS Credentials

```bash
# Configure AWS CLI with your credentials
aws configure

# Verify access
aws sts get-caller-identity
```

### Step 3: Set Up GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**

Add the following secrets:

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `AWS_REGION` | AWS region (e.g., `us-east-1`) | Choose your preferred region |
| `AWS_ROLE_TO_ASSUME` | IAM Role ARN for GitHub Actions | See [AWS Setup](#aws-iam-role-setup) |
| `TF_STATE_BUCKET` | S3 bucket for Terraform state | Create an S3 bucket |
| `TF_STATE_LOCK_TABLE` | DynamoDB table for state locking | Create DynamoDB table |
| `DOCKER_USERNAME` | Your Docker Hub username | From Docker Hub |
| `DOCKER_PASSWORD` | Docker Hub access token | Generate in Docker Hub settings |
| `GRAFANA_ADMIN_PASSWORD` | Password for Grafana admin | Choose a strong password |
| `COSIGN_KEY_ARN` | (Optional) AWS KMS key for signing | Create KMS key in AWS |

---

## 🎯 Deployment Guide

### Phase 1: Infrastructure Setup

#### 1.1 Create AWS Resources

**Create S3 Bucket for Terraform State:**
```bash
aws s3 mb s3://omnishop-tf-state-<your-unique-id> --region us-east-1
aws s3api put-bucket-versioning \
  --bucket omnishop-tf-state-<your-unique-id> \
  --versioning-configuration Status=Enabled
```

**Create DynamoDB Table for State Locking:**
```bash
aws dynamodb create-table \
  --table-name omnishop-tf-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

#### 1.2 AWS IAM Role Setup

Create an IAM role for GitHub Actions with OIDC:

1. Go to **AWS Console** → **IAM** → **Roles** → **Create Role**
2. Select **Web Identity**
3. Identity Provider: `token.actions.githubusercontent.com`
4. Audience: `sts.amazonaws.com`
5. GitHub Organization: `<your-github-username>`
6. Repository: `OmniShop-Enterprise-Platform`
7. Attach policies:
   - `AdministratorAccess` (for demo) or create custom policy
8. Name the role: `GitHubActionsRole`
9. Copy the Role ARN (e.g., `arn:aws:iam::123456789012:role/GitHubActionsRole`)

#### 1.3 Deploy Infrastructure

**Option A: Via GitHub Actions (Recommended)**

1. Push your code to GitHub:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. Go to **Actions** tab in GitHub
3. Run the **Infrastructure Deploy** workflow
4. Wait 10-15 minutes for completion

**Option B: Manual Deployment**

```bash
cd infra/terraform

# Initialize Terraform
terraform init \
  -backend-config="bucket=omnishop-tf-state-<your-unique-id>" \
  -backend-config="key=terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=omnishop-tf-lock"

# Plan infrastructure
terraform plan -var="aws_region=us-east-1"

# Apply infrastructure
terraform apply -var="aws_region=us-east-1" -auto-approve
```

### Phase 2: Configure kubectl Access

After infrastructure is deployed, configure kubectl to access your EKS cluster:

```bash
# Update kubeconfig
aws eks update-kubeconfig \
  --region us-east-1 \
  --name omnishop-eks-cluster

# Verify access
kubectl get nodes
```

You should see your EKS nodes listed.

### Phase 3: Deploy Applications

Applications are automatically deployed via ArgoCD after infrastructure setup. To verify:

```bash
# Check ArgoCD applications
kubectl get applications -n argocd

# Expected output:
# NAME                    SYNC STATUS   HEALTH STATUS
# kube-prometheus-stack   Synced        Healthy
# omnishop-dev            Synced        Healthy
# omnishop-prod           Synced        Healthy
# omnishop-stage          Synced        Healthy
```

---

## 🌐 Accessing Your Services

After deployment, get the external URLs for all services:

```bash
# Get all LoadBalancer services
kubectl get svc -n devsecops
kubectl get svc -n monitoring
kubectl get svc -n argocd
```

### Service URLs

Your services will be accessible at AWS LoadBalancer URLs:

#### **Frontend Application**
```
http://<frontend-loadbalancer-url>
```
- Main application dashboard
- Displays orders and products

#### **Backend APIs**

**Orders Service:**
```
http://<orders-service-loadbalancer-url>
```
Example endpoints:
- `GET /` - Health check
- `GET /api/orders` - List all orders

**Products Service:**
```
http://<products-service-loadbalancer-url>
```
Example endpoints:
- `GET /` - Health check
- `GET /api/products` - List all products

#### **Monitoring - Grafana**
```
http://<grafana-loadbalancer-url>
```
**Login Credentials:**
- Username: `admin`
- Password: `<your-GRAFANA_ADMIN_PASSWORD>`

**Available Dashboards:**
1. Kubernetes Compute Resources / Cluster
2. Kubernetes Compute Resources / Namespace (Pods)
3. Node Exporter / Nodes
4. Prometheus / Overview

#### **GitOps - ArgoCD**
```
http://<argocd-server-loadbalancer-url>
```
**Login Credentials:**
- Username: `admin`
- Password: Get it with this command:
  ```bash
  kubectl get secret argocd-initial-admin-secret -n argocd \
    -o jsonpath="{.data.password}" | base64 -d
  ```

---

## 📊 Monitoring & Observability

### Accessing Grafana Dashboards

1. **Open Grafana** using the LoadBalancer URL
2. **Login** with admin credentials
3. **Navigate to Dashboards:**
   - Click **☰ Menu** (top left)
   - Click **Dashboards**
   - Browse available dashboards

### Key Metrics to Monitor

**Cluster Health:**
- CPU and Memory usage per node
- Pod count and status
- Network I/O

**Application Metrics:**
- Request rate and latency
- Error rates
- Resource consumption

**Custom Dashboards:**

To view your OmniShop services:
1. Go to **Dashboards** → **Kubernetes / Compute Resources / Namespace (Pods)**
2. Select namespace: `devsecops`
3. View metrics for `frontend`, `orders-service`, `products-service`

---

## 🔄 CI/CD Pipelines

### Application CI Pipeline (`app-ci.yml`)

**Triggers:** Changes to `frontend/`, `orders-service/`, `products-service/`

**Steps:**
1. **Build** - Docker images for services
2. **Test** - Run unit tests
3. **Scan** - Trivy security scan
4. **Sign** - Cosign image signing
5. **Push** - Push to Docker Hub

### Infrastructure Deploy Pipeline (`infra-deploy.yml`)

**Triggers:** Changes to `infra/`, `k8s/`

**Steps:**
1. **Terraform Plan** - Preview infrastructure changes
2. **Terraform Apply** - Deploy infrastructure
3. **Configure kubectl** - Set up cluster access
4. **Deploy Monitoring** - Install Prometheus/Grafana
5. **Sync ArgoCD** - Deploy applications

### Manual Workflow Trigger

To manually trigger a workflow:
1. Go to **Actions** tab in GitHub
2. Select the workflow
3. Click **Run workflow**
4. Choose branch and click **Run workflow**

---

## 🔐 Security

### Image Scanning

All container images are scanned with **Trivy** for vulnerabilities:
- Critical and High severity vulnerabilities block the pipeline
- Scan results are available in GitHub Actions logs

### Image Signing

Images are signed with **Cosign** for supply chain security:
- Keyless signing using GitHub OIDC
- Verify signatures before deployment

### Secrets Management

- **GitHub Secrets** - Store sensitive credentials
- **Kubernetes Secrets** - Store cluster credentials
- **AWS Secrets Manager** - (Optional) For production secrets

### Network Security

- **VPC** - Isolated network for EKS cluster
- **Security Groups** - Restrict inbound/outbound traffic
- **IAM Roles** - Least privilege access

---

## 🐛 Troubleshooting

### Common Issues

#### 1. kubectl Access Denied

**Problem:** `error: You must be logged in to the server (Unauthorized)`

**Solution:**
```bash
# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name omnishop-eks-cluster

# Verify IAM user
aws sts get-caller-identity
```

#### 2. ArgoCD Application Not Syncing

**Problem:** Application shows "OutOfSync" status

**Solution:**
```bash
# Manually trigger sync
kubectl patch application <app-name> -n argocd \
  --type merge \
  -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'

# Or use ArgoCD UI
# Click on application → Click "Sync" → Click "Synchronize"
```

#### 3. Grafana Dashboards Not Loading

**Problem:** No dashboards visible in Grafana

**Solution:**
```bash
# Check Grafana pod status
kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana

# Restart Grafana pod
kubectl rollout restart deployment kube-prometheus-stack-grafana -n monitoring

# Wait 2-3 minutes and refresh browser
```

#### 4. LoadBalancer Stuck in Pending

**Problem:** Service EXTERNAL-IP shows `<pending>`

**Solution:**
```bash
# Check service events
kubectl describe svc <service-name> -n <namespace>

# Verify AWS Load Balancer Controller is installed
kubectl get pods -n kube-system | grep aws-load-balancer-controller

# If not installed, it will be created automatically by EKS
```

#### 5. Terraform State Lock

**Problem:** `Error: Error locking state`

**Solution:**
```bash
# Force unlock (use with caution)
terraform force-unlock <lock-id>

# Or delete lock from DynamoDB
aws dynamodb delete-item \
  --table-name omnishop-tf-lock \
  --key '{"LockID":{"S":"<lock-id>"}}'
```

### Getting Help

- **Check Logs:**
  ```bash
  # Application logs
  kubectl logs -n devsecops deployment/<service-name>
  
  # ArgoCD logs
  kubectl logs -n argocd deployment/argocd-server
  
  # Grafana logs
  kubectl logs -n monitoring deployment/kube-prometheus-stack-grafana
  ```

- **Describe Resources:**
  ```bash
  kubectl describe pod <pod-name> -n <namespace>
  kubectl describe svc <service-name> -n <namespace>
  ```

---

## 🧹 Cleanup & Destroy Infrastructure

### ⚠️ Important: Avoid AWS Charges

After practicing with this project, it's **critical** to destroy all resources to avoid ongoing AWS charges. We have provided an automated script to handle this process safely and completely.

### Automated Cleanup Script

The script `infra/scripts/cleanup/nuke.py` automates the following:
1.  **Deletes Kubernetes Load Balancers**: Removes ELBs/ALBs that often block VPC deletion.
2.  **Runs Terraform Destroy**: Destroys the EKS cluster, VPC, and other infrastructure.
3.  **Cleans State Storage**: Deletes the Terraform state S3 bucket and DynamoDB lock table.

#### Usage

1.  **Install Dependencies**:
    ```bash
    pip install boto3
    ```

2.  **Run the Script**:
    ```bash
    python infra/scripts/cleanup/nuke.py \
      --state-bucket omnishop-tf-state-<your-unique-id> \
      --region us-east-1
    ```

    *Replace `<your-unique-id>` with your actual bucket name.*

3.  **Confirm**: Type `yes` when prompted to proceed.

### Manual Verification

After running the script, you can verify that everything is gone:

```bash
# Check for remaining EKS clusters
aws eks list-clusters --region us-east-1

# Check for remaining VPCs (should only see default)
aws ec2 describe-vpcs --region us-east-1 --query "Vpcs[?IsDefault==\`false\`]"

# Check for Load Balancers
aws elb describe-load-balancers --region us-east-1
aws elbv2 describe-load-balancers --region us-east-1
```
aws s3 ls | grep omnishop

# Check for DynamoDB tables
aws dynamodb list-tables \
  --region us-east-1 \
  --query 'TableNames[?contains(@, `omnishop`)]' \
  --output table
```

**Expected Result:** All commands should return empty results or only show default AWS resources.

---

### Step 11: Clean Up Local Files (Optional)

Remove local Terraform state and configuration files:

```bash
# Navigate to project root
cd <project-root>

# Remove Terraform state files
rm -rf infra/terraform/.terraform
rm -f infra/terraform/.terraform.lock.hcl
rm -f infra/terraform/terraform.tfstate*

# Remove kubectl config (optional)
kubectl config delete-context <context-name>
kubectl config delete-cluster omnishop-eks-cluster
```

---

### 📋 Cleanup Checklist

Use this checklist to ensure complete cleanup:

- [ ] Deleted all ArgoCD applications
- [ ] Deleted monitoring namespace
- [ ] Deleted all LoadBalancer services
- [ ] Deleted all AWS load balancers
- [ ] Deleted all target groups
- [ ] Ran `terraform destroy` successfully
- [ ] Deleted security groups (if needed)
- [ ] Deleted network interfaces (if needed)
- [ ] Deleted NAT gateways (if needed)
- [ ] Deleted S3 bucket for Terraform state
- [ ] Deleted DynamoDB table for state locking
- [ ] Deleted IAM roles (optional)
- [ ] Verified no EC2 instances running
- [ ] Verified no EKS clusters exist
- [ ] Verified no extra VPCs exist
- [ ] Verified no load balancers exist
- [ ] Verified no S3 buckets with project name
- [ ] Verified no DynamoDB tables with project name

---

### 💰 Cost Verification

After cleanup, verify you won't incur charges:

1. **Check AWS Billing Dashboard:**
   - Go to [AWS Billing Console](https://console.aws.amazon.com/billing/)
   - Review current month charges
   - Set up billing alerts for future

2. **Enable Cost Explorer:**
   - View costs by service
   - Ensure no ongoing charges from this project

3. **Set Up Budget Alerts:**
   ```bash
   # Create a budget alert (optional)
   aws budgets create-budget \
     --account-id <your-account-id> \
     --budget file://budget.json
   ```

---

### ⚡ Quick Destroy Script

For convenience, here's a complete cleanup script:

```bash
#!/bin/bash
# cleanup.sh - Complete OmniShop infrastructure cleanup

set -e

echo "🧹 Starting OmniShop cleanup..."

# Step 1: Configure kubectl
echo "📋 Step 1: Configuring kubectl..."
aws eks update-kubeconfig --region us-east-1 --name omnishop-eks-cluster || true

# Step 2: Delete ArgoCD applications
echo "📋 Step 2: Deleting ArgoCD applications..."
kubectl delete applications --all -n argocd --ignore-not-found=true

# Step 3: Delete monitoring
echo "📋 Step 3: Deleting monitoring stack..."
kubectl delete namespace monitoring --ignore-not-found=true

# Step 4: Wait for LoadBalancers to be deleted
echo "📋 Step 4: Waiting for LoadBalancers to be deleted..."
sleep 120

# Step 5: Delete remaining LoadBalancers
echo "📋 Step 5: Deleting AWS load balancers..."
for lb_arn in $(aws elbv2 describe-load-balancers --region us-east-1 --query 'LoadBalancers[*].LoadBalancerArn' --output text); do
  echo "Deleting load balancer: $lb_arn"
  aws elbv2 delete-load-balancer --load-balancer-arn "$lb_arn" --region us-east-1 || true
done

# Step 6: Wait for LB deletion
echo "⏳ Waiting for load balancers to be deleted..."
sleep 60

# Step 7: Delete target groups
echo "📋 Step 6: Deleting target groups..."
for tg_arn in $(aws elbv2 describe-target-groups --region us-east-1 --query 'TargetGroups[*].TargetGroupArn' --output text); do
  echo "Deleting target group: $tg_arn"
  aws elbv2 delete-target-group --target-group-arn "$tg_arn" --region us-east-1 || true
done

# Step 8: Terraform destroy
echo "📋 Step 7: Running Terraform destroy..."
cd infra/terraform
terraform destroy -var="aws_region=us-east-1" -auto-approve

# Step 9: Clean up S3 and DynamoDB
echo "📋 Step 8: Cleaning up S3 and DynamoDB..."
aws s3 rm s3://omnishop-tf-state-<your-unique-id> --recursive --region us-east-1 || true
aws s3 rb s3://omnishop-tf-state-<your-unique-id> --region us-east-1 || true
aws dynamodb delete-table --table-name omnishop-tf-lock --region us-east-1 || true

echo "✅ Cleanup complete! Please verify in AWS Console."
```

**To use this script:**
1. Save as `cleanup.sh`
2. Update `<your-unique-id>` with your actual bucket name
3. Make executable: `chmod +x cleanup.sh`
4. Run: `./cleanup.sh`

---

### 🎓 Lessons Learned

After practicing with this project, you should understand:

- ✅ How to provision AWS infrastructure with Terraform
- ✅ How to deploy microservices to Kubernetes
- ✅ How to implement GitOps with ArgoCD
- ✅ How to set up monitoring with Prometheus and Grafana
- ✅ How to implement CI/CD pipelines with GitHub Actions
- ✅ **How to properly destroy cloud infrastructure to avoid costs**

---

**Remember:** Always verify complete cleanup in the AWS Console to ensure you're not incurring unexpected charges!

---

## 📚 Additional Resources

### Documentation

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

### Project Structure

```
.
├── .github/workflows/      # CI/CD pipelines
│   ├── app-ci.yml         # Application build and test
│   └── infra-deploy.yml   # Infrastructure deployment
├── frontend/              # React frontend application
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── orders-service/        # Orders microservice
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── products-service/      # Products microservice
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── infra/                 # Infrastructure as Code
│   └── terraform/
│       ├── main.tf
│       ├── backend.tf
│       └── variables.tf
└── k8s/                   # Kubernetes manifests
    ├── argo/              # ArgoCD applications
    │   ├── applicationset.yaml
    │   └── monitoring.yaml
    └── omnishop-chart/    # Helm chart
        ├── templates/
        └── values.yaml
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is for educational and demonstration purposes.

---

## 🙏 Acknowledgments

- Built with modern DevSecOps best practices
- Inspired by enterprise-grade cloud-native architectures
- Community-driven open-source tools

---

**Happy Deploying! 🚀**

For questions or issues, please open a GitHub issue or contact the maintainers.
