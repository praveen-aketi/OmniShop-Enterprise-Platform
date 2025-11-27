# IAM artifacts for GitHub Actions OIDC and Terraform CI

This folder contains example IAM policy documents and CLI instructions to create the IAM Role used by GitHub Actions (OIDC) and an example Terraform CI policy.

Files
- `trust-policy-github-oidc.json` — OIDC trust policy template. Replace `AWS_ACCOUNT_ID`, `OWNER/REPO` in the file before using.
- `terraform-ci-policy.json` — Example inline policy for a Terraform CI role. Replace `TF_STATE_BUCKET`, `TF_STATE_LOCK_TABLE`, and `AWS_ACCOUNT_ID` placeholders.

Quick CLI examples (PowerShell)

1) Create the IAM role with the trust policy:

```powershell
# Replace placeholders in the JSON first
aws iam create-role --role-name GitHubActionsRole --assume-role-policy-document file://trust-policy-github-oidc.json
```

2) Attach the inline Terraform policy

```powershell
aws iam put-role-policy --role-name GitHubActionsRole --policy-name TerraformCIPolicy --policy-document file://terraform-ci-policy.json
```

3) (Optional) Create an OIDC provider (one-time per account)

```powershell
# You must supply a thumbprint for the provider. Use AWS Console or follow AWS docs to obtain thumbprint.
aws iam create-open-id-connect-provider --url https://token.actions.githubusercontent.com --client-id-list sts.amazonaws.com --thumbprint-list <THUMBPRINT>
```

4) (Optional) Create a KMS key for cosign signing

```powershell
$key=$(aws kms create-key --description "Cosign signing key for GitHub Actions" --key-usage SIGN_VERIFY --origin AWS_KMS | ConvertFrom-Json)
Write-Host "Key ARN: $($key.KeyMetadata.Arn)"

# Update key policy to allow the GitHub role to use the key (or use grants)
```

Validation

- Test role assumption locally by running a simple GitHub Action that uses OIDC to assume the role and calls `aws sts get-caller-identity`.
- Alternatively, use the AWS Console to inspect the role's trust relationship after creation.

Notes & hardening
- Scope the S3 and DynamoDB resources in `terraform-ci-policy.json` to the exact bucket/table names to reduce blast radius.
- Consider splitting responsibilities: a narrow `bootstrap` role (S3 + DynamoDB only) and a separate `terraform` role with broader EKS permissions.
- Use GitHub Environments to store production secrets and require reviewers on environment deployments.

KMS / Cosign setup (exact commands)

1) Create a KMS key and alias (PowerShell)

```powershell
# Create the KMS key
$key=$(aws kms create-key --description "Cosign signing key for GitHub Actions" --key-usage SIGN_VERIFY --origin AWS_KMS | ConvertFrom-Json)
$keyArn = $key.KeyMetadata.Arn
Write-Host "Created KMS Key ARN: $keyArn"

# Create an alias for easier reference
aws kms create-alias --alias-name alias/cosign-github-actions --target-key-id $key.KeyMetadata.KeyId
Write-Host "Alias created: alias/cosign-github-actions"
```

2) Example KMS key policy snippet — add to the key policy to permit the GitHub role to use the key for signing. Replace `AWS_ACCOUNT_ID` and `GITHUB_ROLE_ARN`.

```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "AllowGitHubRoleToUseKey",
			"Effect": "Allow",
			"Principal": {
				"AWS": "arn:aws:iam::AWS_ACCOUNT_ID:role/GitHubActionsRole"
			},
			"Action": [
				"kms:Sign",
				"kms:Verify",
				"kms:GetPublicKey",
				"kms:DescribeKey",
				"kms:CreateGrant",
				"kms:ListGrants",
				"kms:RetireGrant",
				"kms:RevokeGrant"
			],
			"Resource": "*"
		}
	]
}
```

3) (Optional) Create a grant for short-lived usage (cosign may create grants dynamically):

```powershell
aws kms create-grant --key-id $key.KeyMetadata.KeyId --grantee-principal arn:aws:iam::AWS_ACCOUNT_ID:role/GitHubActionsRole --operations Sign Verify CreateGrant
```

Notes:
- Use the alias (`alias/cosign-github-actions`) as the `COSIGN_KEY_ARN` value if you prefer human-readable name; alias usage in cosign may require resolving to the key ARN in scripts.
- Ensure the GitHub role (created with the trust policy) has `kms:CreateGrant` permission if you rely on grants.

