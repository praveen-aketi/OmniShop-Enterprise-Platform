provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "tf_state" {
  bucket = coalesce(var.tf_state_bucket, "${var.cluster_name}-tfstate-${random_id.suffix.hex}")
  acl    = "private"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = {
    Name = "${var.cluster_name}-tfstate"
  }
}

resource "aws_dynamodb_table" "tf_locks" {
  name         = coalesce(var.tf_state_lock_table, "${var.cluster_name}-tf-locks-${random_id.suffix.hex}")
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name = "${var.cluster_name}-tf-locks"
  }
}

output "tf_state_bucket" {
  value = aws_s3_bucket.tf_state.bucket
}

output "tf_state_lock_table" {
  value = aws_dynamodb_table.tf_locks.name
}
