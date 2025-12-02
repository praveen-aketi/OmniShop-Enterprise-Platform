import boto3
import argparse
import sys
import subprocess
import logging
import time
import os
from abc import ABC, abstractmethod

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudCleaner(ABC):
    """Abstract base class for cloud cleaners to ensure multi-cloud support."""
    
    @abstractmethod
    def cleanup_load_balancers(self):
        pass

    @abstractmethod
    def run_terraform_destroy(self):
        pass

    @abstractmethod
    def cleanup_state_store(self):
        pass

class AWSCleaner(CloudCleaner):
    def __init__(self, region, tf_dir, state_bucket, lock_table):
        self.region = region
        self.tf_dir = tf_dir
        self.state_bucket = state_bucket
        self.lock_table = lock_table
        self.ec2 = boto3.client('ec2', region_name=region)
        self.eks = boto3.client('eks', region_name=region)
        self.elb = boto3.client('elb', region_name=region)
        self.elbv2 = boto3.client('elbv2', region_name=region)
        self.s3 = boto3.resource('s3', region_name=region)
        self.dynamodb = boto3.client('dynamodb', region_name=region)

    def cleanup_load_balancers(self):
        """Deletes Classic and Application Load Balancers to free up VPCs."""
        logger.info("Checking for Kubernetes Load Balancers...")
        
        # 1. Classic Load Balancers (ELB)
        try:
            lbs = self.elb.describe_load_balancers().get('LoadBalancerDescriptions', [])
            for lb in lbs:
                name = lb['LoadBalancerName']
                try:
                    logger.info(f"Deleting Classic LB: {name}")
                    self.elb.delete_load_balancer(LoadBalancerName=name)
                except Exception as e:
                    logger.warning(f"Failed to delete Classic LB {name}: {e}")
        except Exception as e:
            logger.warning(f"Error listing Classic LBs: {e}")

        # 2. Application/Network Load Balancers (ALB/NLB)
        try:
            lbs = self.elbv2.describe_load_balancers().get('LoadBalancers', [])
            for lb in lbs:
                arn = lb['LoadBalancerArn']
                try:
                    logger.info(f"Deleting V2 LB: {arn}")
                    self.elbv2.delete_load_balancer(LoadBalancerArn=arn)
                except Exception as e:
                    logger.warning(f"Failed to delete V2 LB {arn}: {e}")
        except Exception as e:
            logger.warning(f"Error listing V2 LBs: {e}")
            
        # Wait for deletion to propagate
        logger.info("Waiting 15s for LB deletion to propagate...")
        time.sleep(15)

    def run_terraform_destroy(self):
        """Runs terraform destroy."""
        if not self.state_bucket:
            logger.warning("No state bucket provided/found. Skipping Terraform Destroy.")
            return

        logger.info("Running Terraform Destroy...")
        try:
            # Initialize
            logger.info("Initializing Terraform...")
            subprocess.run(
                ["terraform", "init", 
                 f"-backend-config=bucket={self.state_bucket}", 
                 f"-backend-config=dynamodb_table={self.lock_table}",
                 f"-backend-config=region={self.region}"],
                cwd=self.tf_dir, check=True, capture_output=True, text=True
            )
            
            # Destroy
            logger.info("Executing Terraform Destroy...")
            subprocess.run(
                ["terraform", "destroy", "-auto-approve", f"-var=aws_region={self.region}"],
                cwd=self.tf_dir, check=True
            )
            logger.info("Terraform Destroy completed successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Terraform command failed. This might happen if the state bucket is missing or infrastructure is already deleted.")
            if hasattr(e, 'stderr'):
                logger.error(f"Error output: {e.stderr}")
            logger.info("Skipping Terraform Destroy and proceeding to next step...")
        except Exception as e:
             logger.error(f"Unexpected error during Terraform Destroy: {e}")
             logger.info("Skipping Terraform Destroy...")

    def cleanup_state_store(self):
        """Deletes the S3 bucket and DynamoDB table used for Terraform state."""
        logger.info("Cleaning up Terraform State Storage...")
        
        # 1. Delete S3 Bucket
        if self.state_bucket:
            try:
                bucket = self.s3.Bucket(self.state_bucket)
                # Check if bucket exists by attempting to load it
                try:
                    self.s3.meta.client.head_bucket(Bucket=self.state_bucket)
                    logger.info(f"Deleting all versions in bucket {self.state_bucket}...")
                    bucket.object_versions.delete()
                    logger.info(f"Deleting bucket {self.state_bucket}...")
                    bucket.delete()
                    logger.info("Bucket deleted.")
                except self.s3.meta.client.exceptions.ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == '404':
                        logger.info(f"Bucket {self.state_bucket} not found (already deleted).")
                    else:
                        logger.warning(f"Error checking bucket: {e}")
            except Exception as e:
                logger.warning(f"Error processing S3 bucket cleanup: {e}")
        else:
            logger.info("No state bucket to clean up.")

        # 2. Delete DynamoDB Table
        try:
            self.dynamodb.delete_table(TableName=self.lock_table)
            logger.info(f"Deleting DynamoDB table {self.lock_table}...")
            
            waiter = self.dynamodb.get_waiter('table_not_exists')
            waiter.wait(TableName=self.lock_table)
            logger.info("DynamoDB table deleted.")
        except self.dynamodb.exceptions.ResourceNotFoundException:
            logger.info(f"DynamoDB table {self.lock_table} not found (already deleted).")
        except Exception as e:
            logger.warning(f"Error deleting DynamoDB table: {e}")

    def verify_cleanup(self):
        """Verifies if resources are actually deleted."""
        logger.info("\n🔍 Verifying Cleanup Status...")
        
        status_report = []
        
        # 1. Check EKS Clusters
        try:
            clusters = self.eks.list_clusters().get('clusters', [])
            if not clusters:
                status_report.append("✅ EKS Clusters: Deleted")
            else:
                status_report.append(f"❌ EKS Clusters: {len(clusters)} remaining")
        except Exception as e:
            logger.warning(f"Error checking EKS clusters: {e}")
            status_report.append("⚠️ EKS Clusters: Check Failed")
        
        # 2. Check Load Balancers
        clb_count = len(self.elb.describe_load_balancers().get('LoadBalancerDescriptions', []))
        alb_count = len(self.elbv2.describe_load_balancers().get('LoadBalancers', []))
        
        if clb_count + alb_count == 0:
            status_report.append("✅ Load Balancers: Deleted")
        else:
            status_report.append(f"❌ Load Balancers: {clb_count + alb_count} remaining")

        # 3. Check VPCs (Non-default)
        vpcs = self.ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['false']}])['Vpcs']
        if not vpcs:
            status_report.append("✅ Custom VPCs: Deleted")
        else:
            status_report.append(f"❌ Custom VPCs: {len(vpcs)} remaining")
            
        # 4. Check Subnets (Non-default)
        if vpcs:
            vpc_ids = [v['VpcId'] for v in vpcs]
            subnets = self.ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': vpc_ids}])['Subnets']
            status_report.append(f"❌ Subnets: {len(subnets)} remaining (in custom VPCs)")
        else:
            status_report.append("✅ Subnets: Deleted")

        # 5. Check NAT Gateways
        nats = self.ec2.describe_nat_gateways(Filters=[{'Name': 'state', 'Values': ['available', 'pending']}])['NatGateways']
        if not nats:
            status_report.append("✅ NAT Gateways: Deleted")
        else:
            status_report.append(f"❌ NAT Gateways: {len(nats)} remaining")

        # Print Report
        print("\n" + "="*40)
        print("   CLEANUP VERIFICATION REPORT")
        print("="*40)
        for line in status_report:
            print(line)
        print("="*40 + "\n")

def main():
    # Calculate absolute path to terraform dir relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_tf_dir = os.path.abspath(os.path.join(script_dir, "../../terraform"))

    parser = argparse.ArgumentParser(description="Automated Infrastructure Cleanup")
    parser.add_argument("--cloud", choices=['aws'], default='aws', help="Cloud provider")
    parser.add_argument("--region", default='us-east-1', help="AWS Region")
    parser.add_argument("--tf-dir", default=default_tf_dir, help="Path to Terraform directory")
    parser.add_argument("--state-bucket", help="Terraform State S3 Bucket Name (optional, will auto-discover if omitted)")
    parser.add_argument("--lock-table", default='omnishop-tf-lock', help="Terraform Lock DynamoDB Table")
    
    args = parser.parse_args()

    # Auto-discover state bucket if not provided
    if not args.state_bucket:
        print("🔍 Searching for Terraform state bucket...")
        try:
            s3_client = boto3.client('s3', region_name=args.region)
            response = s3_client.list_buckets()
            candidates = [b['Name'] for b in response.get('Buckets', []) if 'omnishop-tf-state' in b['Name']]
            
            if len(candidates) == 1:
                args.state_bucket = candidates[0]
                print(f"✅ Found state bucket: {args.state_bucket}")
            elif len(candidates) > 1:
                print("⚠️ Found multiple candidate buckets:")
                for i, b in enumerate(candidates):
                    print(f"  {i+1}. {b}")
                selection = input("Select bucket number to use (or press Enter to skip state cleanup): ")
                if selection.isdigit() and 1 <= int(selection) <= len(candidates):
                    args.state_bucket = candidates[int(selection)-1]
                else:
                    print("⚠️ No bucket selected. Terraform destroy and state cleanup will be skipped.")
            else:
                print("⚠️ No bucket found matching 'omnishop-tf-state'. Terraform destroy and state cleanup will be skipped.")
        except Exception as e:
            print(f"⚠️ Error during bucket discovery: {e}")

    if args.cloud == 'aws':
        cleaner = AWSCleaner(args.region, args.tf_dir, args.state_bucket, args.lock_table)
        
        bucket_msg = args.state_bucket if args.state_bucket else "NONE (Skipping TF Destroy)"
        print(f"⚠️  WARNING: This will DESTROY all infrastructure in {args.region}.")
        print(f"   State Bucket: {bucket_msg}")
        print(f"   Terraform Directory: {args.tf_dir}")
        
        confirm = input("Are you sure you want to proceed? (yes/no): ")
        
        if confirm.lower() == 'yes':
            cleaner.cleanup_load_balancers()
            cleaner.run_terraform_destroy()
            cleaner.cleanup_state_store()
            cleaner.verify_cleanup()
            logger.info("Cleanup sequence complete.")
        else:
            logger.info("Cleanup cancelled.")

if __name__ == "__main__":
    main()
