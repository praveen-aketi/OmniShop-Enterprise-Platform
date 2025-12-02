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

    def force_delete_infrastructure(self):
        """Force deletes infrastructure when Terraform state is missing."""
        logger.info("⚠️  STARTING FORCE DELETE: Scanning for lingering resources...")
        
        # 0. Delete EKS Clusters
        logger.info("Checking for EKS Clusters...")
        try:
            clusters = self.eks.list_clusters().get('clusters', [])
            for cluster_name in clusters:
                if 'devsecops' in cluster_name or 'omnishop' in cluster_name:
                    logger.info(f"Deleting EKS Cluster: {cluster_name}")
                    try:
                        self.eks.delete_cluster(name=cluster_name)
                        # Wait for deletion
                        logger.info(f"Waiting for cluster {cluster_name} to delete (this takes time)...")
                        waiter = self.eks.get_waiter('cluster_deleted')
                        waiter.wait(name=cluster_name)
                        logger.info(f"Cluster {cluster_name} deleted.")
                    except Exception as e:
                        logger.error(f"Failed to delete cluster {cluster_name}: {e}")
        except Exception as e:
            logger.warning(f"Error checking/deleting EKS clusters: {e}")

        # 1. Delete CloudWatch Log Groups
        logger.info("Checking for CloudWatch Log Groups...")
        try:
            logs = boto3.client('logs', region_name=self.region)
            log_groups = logs.describe_log_groups(logGroupNamePrefix='/aws/eks/')['logGroups']
            for lg in log_groups:
                if 'devsecops' in lg['logGroupName'] or 'omnishop' in lg['logGroupName']:
                    logger.info(f"Deleting Log Group: {lg['logGroupName']}")
                    logs.delete_log_group(logGroupName=lg['logGroupName'])
        except Exception as e:
            logger.warning(f"Error deleting log groups: {e}")

        # Find VPCs matching project tags
        vpcs = self.ec2.describe_vpcs(Filters=[
            {'Name': 'tag:Name', 'Values': ['*devsecops*', '*omnishop*', '*eks*']}
        ])['Vpcs']
        
        if not vpcs:
            logger.info("No project VPCs found for force deletion.")
        
        for vpc in vpcs:
            vpc_id = vpc['VpcId']
            logger.info(f"💣 Nuke target acquired: VPC {vpc_id}")
            
            # 2. Terminate EC2 Instances
            instances = self.ec2.describe_instances(Filters=[
                {'Name': 'vpc-id', 'Values': [vpc_id]},
                {'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'stopping', 'pending']}
            ])
            instance_ids = [i['InstanceId'] for r in instances['Reservations'] for i in r['Instances']]
            
            if instance_ids:
                logger.info(f"Terminating {len(instance_ids)} EC2 instances: {instance_ids}")
                self.ec2.terminate_instances(InstanceIds=instance_ids)
                
                logger.info("Waiting for instances to terminate...")
                waiter = self.ec2.get_waiter('instance_terminated')
                waiter.wait(InstanceIds=instance_ids)
                logger.info("Instances terminated.")

            # 3. Delete NAT Gateways
            nats = self.ec2.describe_nat_gateways(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['NatGateways']
            for nat in nats:
                if nat['State'] != 'deleted':
                    logger.info(f"Deleting NAT Gateway: {nat['NatGatewayId']}")
                    self.ec2.delete_nat_gateway(NatGatewayId=nat['NatGatewayId'])
            
            # Wait for NATs to delete (critical for dependencies)
            if nats:
                logger.info("Waiting for NAT Gateways to delete...")
                while True:
                    remaining = self.ec2.describe_nat_gateways(Filters=[
                        {'Name': 'vpc-id', 'Values': [vpc_id]},
                        {'Name': 'state', 'Values': ['pending', 'available', 'deleting']}
                    ])['NatGateways']
                    if not remaining:
                        break
                    time.sleep(5)

            # 4. Release Elastic IPs
            # Note: EIPs are often associated with NAT Gateways, so release them after NAT deletion
            eips = self.ec2.describe_addresses(Filters=[{'Name': 'tag:Name', 'Values': ['*devsecops*', '*omnishop*']}])['Addresses']
            for eip in eips:
                logger.info(f"Releasing Elastic IP: {eip['AllocationId']}")
                try:
                    self.ec2.release_address(AllocationId=eip['AllocationId'])
                except Exception as e:
                    logger.warning(f"Failed to release EIP {eip['AllocationId']}: {e}")

            # 5. Delete Internet Gateways
            igws = self.ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])['InternetGateways']
            for igw in igws:
                logger.info(f"Detaching and Deleting IGW: {igw['InternetGatewayId']}")
                self.ec2.detach_internet_gateway(InternetGatewayId=igw['InternetGatewayId'], VpcId=vpc_id)
                self.ec2.delete_internet_gateway(InternetGatewayId=igw['InternetGatewayId'])

            # 6. Delete Subnets
            subnets = self.ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
            for subnet in subnets:
                logger.info(f"Deleting Subnet: {subnet['SubnetId']}")
                try:
                    self.ec2.delete_subnet(SubnetId=subnet['SubnetId'])
                except Exception as e:
                    logger.warning(f"Failed to delete subnet {subnet['SubnetId']}: {e}")

            # 7. Delete Route Tables (except main)
            rts = self.ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['RouteTables']
            for rt in rts:
                if not any(assoc['Main'] for assoc in rt['Associations']):
                    logger.info(f"Deleting Route Table: {rt['RouteTableId']}")
                    try:
                        self.ec2.delete_route_table(RouteTableId=rt['RouteTableId'])
                    except Exception as e:
                        logger.warning(f"Failed to delete RT {rt['RouteTableId']}: {e}")

            # 8. Delete Security Groups
            # We need to revoke all rules first to break cyclic dependencies
            sgs = self.ec2.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['SecurityGroups']
            for sg in sgs:
                if sg['GroupName'] == 'default': continue
                logger.info(f"Revoking rules for SG: {sg['GroupId']}")
                try:
                    if sg['IpPermissions']:
                        self.ec2.revoke_security_group_ingress(GroupId=sg['GroupId'], IpPermissions=sg['IpPermissions'])
                    if sg['IpPermissionsEgress']:
                        self.ec2.revoke_security_group_egress(GroupId=sg['GroupId'], IpPermissions=sg['IpPermissionsEgress'])
                except Exception as e:
                    logger.warning(f"Error revoking rules for {sg['GroupId']}: {e}")
            
            time.sleep(5) # Wait for revocation
            
            for sg in sgs:
                if sg['GroupName'] == 'default': continue
                logger.info(f"Deleting SG: {sg['GroupId']}")
                try:
                    self.ec2.delete_security_group(GroupId=sg['GroupId'])
                except Exception as e:
                    logger.warning(f"Failed to delete SG {sg['GroupId']}: {e}")

            # 9. Delete VPC
            logger.info(f"Deleting VPC: {vpc_id}")
            try:
                self.ec2.delete_vpc(VpcId=vpc_id)
                logger.info("VPC Deleted.")
            except Exception as e:
                logger.error(f"Failed to delete VPC {vpc_id}: {e}")

        # 10. Delete IAM Roles
        # This is outside the VPC loop as roles are global
        iam = boto3.client('iam')
        try:
            roles = iam.list_roles()['Roles']
            for role in roles:
                if 'devsecops' in role['RoleName'] or 'omnishop' in role['RoleName']:
                    logger.info(f"Deleting IAM Role: {role['RoleName']}")
                    try:
                        # Detach all policies first
                        policies = iam.list_attached_role_policies(RoleName=role['RoleName'])['AttachedPolicies']
                        for p in policies:
                            iam.detach_role_policy(RoleName=role['RoleName'], PolicyArn=p['PolicyArn'])
                        
                        # Delete inline policies
                        inline_policies = iam.list_role_policies(RoleName=role['RoleName'])['PolicyNames']
                        for p in inline_policies:
                            iam.delete_role_policy(RoleName=role['RoleName'], PolicyName=p)

                        iam.delete_role(RoleName=role['RoleName'])
                    except Exception as e:
                        logger.warning(f"Failed to delete role {role['RoleName']}: {e}")
        except Exception as e:
            logger.warning(f"Error cleaning up IAM roles: {e}")

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
    parser.add_argument("--force", action='store_true', help="Force delete resources without Terraform state")
    
    args = parser.parse_args()

    # Auto-discover state bucket if not provided
    if not args.state_bucket and not args.force:
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
        print(f"   Force Mode: {'ENABLED' if args.force else 'DISABLED'}")
        
        confirm = input("Are you sure you want to proceed? (yes/no): ")
        
        if confirm.lower() == 'yes':
            cleaner.cleanup_load_balancers()
            
            if args.force:
                cleaner.force_delete_infrastructure()
            else:
                cleaner.run_terraform_destroy()
                
                # If TF destroy was skipped or failed, ask for force delete
                if not args.state_bucket:
                    force_confirm = input("\nTerraform state missing. Do you want to FORCE DELETE remaining resources (VPCs, Subnets, etc.)? (yes/no): ")
                    if force_confirm.lower() == 'yes':
                        cleaner.force_delete_infrastructure()

            cleaner.cleanup_state_store()
            cleaner.verify_cleanup()
            logger.info("Cleanup sequence complete.")
        else:
            logger.info("Cleanup cancelled.")

if __name__ == "__main__":
    main()
