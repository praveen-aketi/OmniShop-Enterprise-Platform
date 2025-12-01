# Check if Docker is running
if (!(Get-Process docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not running. Please start Docker Desktop first."
    exit 1
}

# Check if Kind is installed
if (!(Get-Command kind -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Kind..."
    choco install kind -y
}

# Create Cluster
Write-Host "Creating Local Kubernetes Cluster..."
kind create cluster --name omnishop-local

# Install ArgoCD
Write-Host "Installing ArgoCD..."
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD
Write-Host "Waiting for ArgoCD..."
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=300s

# Apply ApplicationSet (Point to local path or git)
# For local dev, we usually just apply the charts directly or port-forward
Write-Host "Cluster Ready!"
Write-Host "You can now use 'kubectl' to interact with your local cluster."
