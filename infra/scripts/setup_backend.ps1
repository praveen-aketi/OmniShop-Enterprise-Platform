param(
    [string]$Region = "us-east-1",
    [string]$GitHubOrg = "praveen-aketi",
    [string]$GitHubRepo = "DevSecOps-practices", # Updated to match your folder name/likely repo
    [string]$BucketName = "omnishop-tf-state-$((Get-Random))",
    [string]$DynamoTableName = "omnishop-tf-lock"
)

$ErrorActionPreference = "Stop"

Write-Host "Checking AWS identity..."
aws sts get-caller-identity
if ($LASTEXITCODE -ne 0) {
    Write-Error "Please run 'aws configure' to set up your credentials first."
}

# 1. Create S3 Bucket
Write-Host "`n--- Setting up S3 Bucket: $BucketName ---"
if (aws s3api head-bucket --bucket $BucketName 2>$null) {
    Write-Host "Bucket $BucketName already exists."
} else {
    aws s3api create-bucket --bucket $BucketName --region $Region
    if ($Region -ne "us-east-1") {
        aws s3api create-bucket --bucket $BucketName --region $Region --create-bucket-configuration LocationConstraint=$Region
    }
    aws s3api put-bucket-versioning --bucket $BucketName --versioning-configuration Status=Enabled
    Write-Host "Bucket created."
}

# 2. Create DynamoDB Table
Write-Host "`n--- Setting up DynamoDB Table: $DynamoTableName ---"
$table = aws dynamodb list-tables --query "TableNames[? @ == '$DynamoTableName']" --output text
if ($table) {
    Write-Host "Table $DynamoTableName already exists."
} else {
    aws dynamodb create-table --table-name $DynamoTableName `
        --attribute-definitions AttributeName=LockID,AttributeType=S `
        --key-schema AttributeName=LockID,KeyType=HASH `
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 `
        --region $Region
    Write-Host "Table created."
}

# 3. Setup OIDC Provider
Write-Host "`n--- Setting up OIDC Provider ---"
$oidcUrl = "https://token.actions.githubusercontent.com"
$oidcArn = aws iam list-open-id-connect-providers --output text --query "OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')].Arn"

if (-not $oidcArn) {
    # Thumbprint for GitHub Actions (valid until 2031)
    $thumbprint = "6938fd4d98bab03faadb97b34396831e3780aea1"
    $oidcArn = aws iam create-open-id-connect-provider --url $oidcUrl --client-id-list "sts.amazonaws.com" --thumbprint-list $thumbprint --query "OpenIDConnectProviderArn" --output text
    Write-Host "OIDC Provider created: $oidcArn"
} else {
    Write-Host "OIDC Provider already exists: $oidcArn"
}

# 4. Create IAM Role
$RoleName = "GitHubAction-OmniShop-Role"
Write-Host "`n--- Setting up IAM Role: $RoleName ---"

$TrustPolicy = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "$oidcArn"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:$($GitHubOrg)/$($GitHubRepo):*"
                },
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                }
            }
        }
    ]
}
"@

try {
    aws iam get-role --role-name $RoleName > $null 2>&1
    aws iam update-assume-role-policy --role-name $RoleName --policy-document $TrustPolicy
    Write-Host "Role exists. Updated trust policy."
} catch {
    aws iam create-role --role-name $RoleName --assume-role-policy-document $TrustPolicy
    Write-Host "Role created."
}

# Attach AdministratorAccess (For demo purposes - refine for production)
aws iam attach-role-policy --role-name $RoleName --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
$RoleArn = aws iam get-role --role-name $RoleName --query "Role.Arn" --output text

Write-Host "`n`n========================================================"
Write-Host "   SETUP COMPLETE! ADD THESE SECRETS TO GITHUB"
Write-Host "========================================================"
Write-Host "AWS_REGION          : $Region"
Write-Host "AWS_ROLE_TO_ASSUME  : $RoleArn"
Write-Host "TF_STATE_BUCKET     : $BucketName"
Write-Host "TF_STATE_LOCK_TABLE : $DynamoTableName"
Write-Host "========================================================"
