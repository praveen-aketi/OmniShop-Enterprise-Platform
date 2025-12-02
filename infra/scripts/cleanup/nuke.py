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
    def __init__(self, region, tf_dir, state_bucket, lock_table, project_identifiers):
        self.region = region
        self.tf_dir = tf_dir
        self.state_bucket = state_bucket
        self.lock_table = lock_table
        self.project_identifiers = project_identifiers
        self.ec2 = boto3.client('ec2', region_name=region)
        self.eks = boto3.client('eks', region_name=region)
        self.elb = boto3.client('elb', region_name=region)
        self.elbv2 = boto3.client('elbv2', region_name=region)
        self.s3 = boto3.resource('s3', region_name=region)
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.kms = boto3.client('kms', region_name=region)

    def _is_project_resource(self, name):
        """Helper to check if a resource name matches any project identifier."""
        if not name: return False
        return any(pid in name for pid in self.project_identifiers)

    def cleanup_kms(self):
        """Deletes KMS keys and aliases associated with the project."""
        logger.info("Checking for KMS Keys and Aliases...")
        try:
            # List aliases
            paginator = self.kms.get_paginator('list_aliases')
            for page in paginator.paginate():
                for alias in page['Aliases']:
                    alias_name = alias.get('AliasName', '')
                    # Check if alias matches project (e.g. alias/eks/devsecops-cluster)
                    if self._is_project_resource(alias_name):
                        logger.info(f"Deleting KMS Alias: {alias_name}")
                        try:
                            self.kms.delete_alias(AliasName=alias_name)
                        except Exception as e:
                            logger.warning(f"Failed to delete alias {alias_name}: {e}")
                        
                        # Optionally schedule key deletion if it's a target key (be careful here)
                        # For EKS, the key is usually created by the module. 
                        # If we delete the alias, we should probably schedule the key for deletion too 
                        # to avoid leaving orphaned keys (cost money).
                        if 'TargetKeyId' in alias:
                            key_id = alias['TargetKeyId']
                            try:
                                key_info = self.kms.describe_key(KeyId=key_id)['KeyMetadata']
                                if key_info['KeyState'] not in ['PendingDeletion', 'Unavailable']:
                                    logger.info(f"Scheduling KMS Key deletion: {key_id}")
                                    self.kms.schedule_key_deletion(KeyId=key_id, PendingWindowInDays=7)
                            except Exception as e:
                                logger.warning(f"Failed to schedule key deletion for {key_id}: {e}")

        except Exception as e:
            logger.warning(f"Error cleaning up KMS: {e}")

    def cleanup_load_balancers(self):
        """Deletes Classic and Application Load Balancers to free up VPCs."""
        logger.info("Checking for Kubernetes Load Balancers...")
        
        # 1. Classic Load Balancers (ELB)
        try:
            lbs = self.elb.describe_load_balancers().get('LoadBalancerDescriptions', [])
            for lb in lbs:
                name = lb['LoadBalancerName']
                # Clean up if it matches project or is a k8s LB (often starts with a hash, so we might need to be aggressive or check tags)
                # For safety, let's rely on tags if possible, or assume all LBs in a sandbox account are fair game if they look like k8s ones.
                # But to be safe for "any project", let's check tags or name match.
                # K8s LBs usually don't have the project name in the LB name itself, but in tags.
                
                is_target = False
                try:
                    tags = self.elb.describe_tags(LoadBalancerNames=[name])['TagDescriptions'][0]['Tags']
                    is_target = any(t['Key'] == 'kubernetes.io/cluster/' + pid for pid in self.project_identifiers for t in tags) or \
                                any(pid in t['Value'] for pid in self.project_identifiers for t in tags)
                except:
                    pass
                
                # Fallback: if we are in force mode or it matches name
                if self._is_project_resource(name) or is_target:
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
                name = lb['LoadBalancerName']
                
                is_target = False
                try:
                    tags = self.elbv2.describe_tags(ResourceArns=[arn])['TagDescriptions'][0]['Tags']
                    is_target = any(pid in t['Value'] for pid in self.project_identifiers for t in tags) or \
                                any('kubernetes.io/cluster' in t['Key'] for t in tags) # Broad check for k8s LBs
                except:
                    pass

                if self._is_project_resource(name) or is_target:
                    try:
                        logger.info(f"Deleting V2 LB: {name}")
                        self.elbv2.delete_load_balancer(LoadBalancerArn=arn)
                    except Exception as e:
                        logger.warning(f"Failed to delete V2 LB {name}: {e}")
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
        logger.info(f"⚠️  STARTING FORCE DELETE for projects: {self.project_identifiers}")
        
        # 0. Delete EKS Clusters
        logger.info("Checking for EKS Clusters...")
        try:
            clusters = self.eks.list_clusters().get('clusters', [])
            for cluster_name in clusters:
                if self._is_project_resource(cluster_name):
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
                if self._is_project_resource(lg['logGroupName']):
                    logger.info(f"Deleting Log Group: {lg['logGroupName']}")
                    logs.delete_log_group(logGroupName=lg['logGroupName'])
        except Exception as e:
            logger.warning(f"Error deleting log groups: {e}")

        # Find VPCs matching project tags
        # We look for Name tags containing any of the project identifiers
        filters = [{'Name': 'tag:Name', 'Values': [f'*{pid}*' for pid in self.project_identifiers]}]
        # Also add 'eks' to catch generic EKS VPCs if they are tagged with project name elsewhere, 
        # but let's stick to project identifiers to be safe for "any project".
        
        vpcs = self.ec2.describe_vpcs(Filters=filters)['Vpcs']
        
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
            eips = self.ec2.describe_addresses(Filters=[{'Name': 'tag:Name', 'Values': [f'*{pid}*' for pid in self.project_identifiers]}])['Addresses']
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

        # 10. Delete IAM Roles, Policies, and OIDC Providers
        iam = boto3.client('iam')
        
        # A. Delete OIDC Providers
        logger.info("Checking for OIDC Providers...")
        try:
            oidc_providers = iam.list_open_id_connect_providers()['OpenIDConnectProviderList']
            for provider in oidc_providers:
                # Get tags or check ARN to identify if it belongs to our cluster
                arn = provider['Arn']
                try:
                    tags = iam.list_open_id_connect_provider_tags(OpenIDConnectProviderArn=arn)['Tags']
                    is_project_oidc = any(t['Key'] == 'Name' and self._is_project_resource(t['Value']) for t in tags)
                    
                    if is_project_oidc or 'eks' in arn: 
                        logger.info(f"Deleting OIDC Provider: {arn}")
                        iam.delete_open_id_connect_provider(OpenIDConnectProviderArn=arn)
                except Exception as e:
                    logger.warning(f"Failed to process OIDC provider {arn}: {e}")
        except Exception as e:
            logger.warning(f"Error cleaning up OIDC providers: {e}")

        # B. Delete IAM Roles
        logger.info("Checking for IAM Roles...")
        try:
            roles = iam.list_roles()['Roles']
            for role in roles:
                if self._is_project_resource(role['RoleName']) or 'eks-cluster-role' in role['RoleName']:
                    logger.info(f"Deleting IAM Role: {role['RoleName']}")
                    try:
                        # Detach all managed policies
                        policies = iam.list_attached_role_policies(RoleName=role['RoleName'])['AttachedPolicies']
                        for p in policies:
                            iam.detach_role_policy(RoleName=role['RoleName'], PolicyArn=p['PolicyArn'])
                        
                        # Delete inline policies
                        inline_policies = iam.list_role_policies(RoleName=role['RoleName'])['PolicyNames']
                        for p in inline_policies:
                            iam.delete_role_policy(RoleName=role['RoleName'], PolicyName=p)
                        
                        # Remove from Instance Profiles
                        profiles = iam.list_instance_profiles_for_role(RoleName=role['RoleName'])['InstanceProfiles']
                        for profile in profiles:
                            iam.remove_role_from_instance_profile(InstanceProfileName=profile['InstanceProfileName'], RoleName=role['RoleName'])
                            # Try to delete the profile too if empty
                            try:
                                iam.delete_instance_profile(InstanceProfileName=profile['InstanceProfileName'])
                            except:
                                pass

                        iam.delete_role(RoleName=role['RoleName'])
                    except Exception as e:
                        logger.warning(f"Failed to delete role {role['RoleName']}: {e}")
        except Exception as e:
            logger.warning(f"Error cleaning up IAM roles: {e}")

        # C. Delete Customer Managed Policies
        logger.info("Checking for Custom IAM Policies...")
        try:
            # Scope to Local (Customer Managed) policies
            policies = iam.list_policies(Scope='Local')['Policies']
            for p in policies:
                if self._is_project_resource(p['PolicyName']) or 'AWSLoadBalancerController' in p['PolicyName']:
                    logger.info(f"Deleting IAM Policy: {p['PolicyName']}")
                    try:
                        # Delete policy versions (except default)
                        versions = iam.list_policy_versions(PolicyArn=p['Arn'])['Versions']
                        for v in versions:
                            if not v['IsDefaultVersion']:
                                iam.delete_policy_version(PolicyArn=p['Arn'], VersionId=v['VersionId'])
                        
                        iam.delete_policy(PolicyArn=p['Arn'])
                    except Exception as e:
                        logger.warning(f"Failed to delete policy {p['PolicyName']}: {e}")
        except Exception as e:
            logger.warning(f"Error cleaning up IAM policies: {e}")

        # 11. Delete KMS Keys/Aliases
        self.cleanup_kms()

    def verify_cleanup(self):
        """Verifies if resources are actually deleted."""
        logger.info("\n🔍 Verifying Cleanup Status...")
        
        status_report = []
        
        def check_status(resource_name, count, is_deleting=False):
            if count == 0:
                return f"✅ {resource_name}: Deleted"
            elif is_deleting:
                return f"⏳ {resource_name}: {count} Deleting (in progress)"
            else:
                return f"❌ {resource_name}: {count} Remaining (Action Required)"

        # 1. Check EKS Clusters
        try:
            clusters = self.eks.list_clusters().get('clusters', [])
            project_clusters = [c for c in clusters if self._is_project_resource(c)]
            status_report.append(check_status("EKS Clusters", len(project_clusters)))
        except Exception as e:
            status_report.append("⚠️ EKS Clusters: Check Failed")
        
        # 2. Check Load Balancers
        # (Simplified check: just count all LBs as it's hard to filter by project without tags sometimes)
        clb = self.elb.describe_load_balancers().get('LoadBalancerDescriptions', [])
        alb = self.elbv2.describe_load_balancers().get('LoadBalancers', [])
        status_report.append(check_status("Load Balancers", len(clb) + len(alb)))

        # 3. Check NAT Gateways (Filter for non-deleted)
        nats_active = self.ec2.describe_nat_gateways(Filters=[{'Name': 'state', 'Values': ['available', 'pending']}])['NatGateways']
        nats_deleting = self.ec2.describe_nat_gateways(Filters=[{'Name': 'state', 'Values': ['deleting']}])['NatGateways']
        
        if nats_active:
            status_report.append(f"❌ NAT Gateways: {len(nats_active)} Active")
        elif nats_deleting:
            status_report.append(f"⏳ NAT Gateways: {len(nats_deleting)} Deleting...")
        else:
            status_report.append("✅ NAT Gateways: Deleted")

        # 4. Check VPCs
        vpcs = self.ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['false']}])['Vpcs']
        status_report.append(check_status("Custom VPCs", len(vpcs)))
            
        # 5. Check Subnets
        if vpcs:
            vpc_ids = [v['VpcId'] for v in vpcs]
            subnets = self.ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': vpc_ids}])['Subnets']
            status_report.append(check_status("Subnets", len(subnets)))
        else:
            status_report.append("✅ Subnets: Deleted")

        # 6. Check Security Groups (non-default)
        if vpcs:
            vpc_ids = [v['VpcId'] for v in vpcs]
            sgs = self.ec2.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': vpc_ids}])['SecurityGroups']
            non_default_sgs = [sg for sg in sgs if sg['GroupName'] != 'default']
            status_report.append(check_status("Security Groups", len(non_default_sgs)))
        else:
            status_report.append("✅ Security Groups: Deleted")

        # 7. Check Network ACLs (non-default)
        if vpcs:
            vpc_ids = [v['VpcId'] for v in vpcs]
            nacls = self.ec2.describe_network_acls(Filters=[{'Name': 'vpc-id', 'Values': vpc_ids}])['NetworkAcls']
            non_default_nacls = [n for n in nacls if not n['IsDefault']]
            status_report.append(check_status("Network ACLs", len(non_default_nacls)))
        else:
            status_report.append("✅ Network ACLs: Deleted")

        # 8. Check IAM Roles & Policies
        iam = boto3.client('iam')
        try:
            roles = iam.list_roles()['Roles']
            project_roles = [r for r in roles if self._is_project_resource(r['RoleName'])]
            status_report.append(check_status("IAM Roles", len(project_roles)))
            
            policies = iam.list_policies(Scope='Local')['Policies']
            project_policies = [p for p in policies if self._is_project_resource(p['PolicyName'])]
            status_report.append(check_status("IAM Policies", len(project_policies)))
        except Exception:
            status_report.append("⚠️ IAM Checks: Failed")

        # Print Report
        print("\n" + "="*50)
        print("   CLEANUP VERIFICATION REPORT")
        print("="*50)
        for line in status_report:
            print(line)
        print("="*50)
        print("ℹ️  NOTE: Resources in 'Deleted' state may remain visible")
        print("    in the AWS Console for ~1 hour. This is normal.")
        print("="*50 + "\n")

def get_tf_variable_default(tf_dir, var_name):
    """Reads variables.tf to find the default value of a variable."""
    var_file = os.path.join(tf_dir, "variables.tf")
    try:
        with open(var_file, 'r') as f:
            content = f.read()
            # Simple regex to find variable block and default value
            # variable "cluster_name" { ... default = "value" ... }
            import re
            match = re.search(r'variable\s+"' + var_name + r'"\s*{[^}]*default\s*=\s*"([^"]+)"', content, re.DOTALL)
            if match:
                return match.group(1)
    except Exception as e:
        logger.warning(f"Could not read {var_name} from variables.tf: {e}")
    return None

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
    parser.add_argument("--projects", help="Comma-separated list of project identifiers (optional, defaults to auto-detected names)")
    
    args = parser.parse_args()
    
    # 1. Start with 'omnishop' as the base project name
    project_identifiers = ['omnishop']
    
    # 2. Auto-detect cluster name from Terraform config
    detected_cluster_name = get_tf_variable_default(args.tf_dir, "cluster_name")
    if detected_cluster_name:
        print(f"🔍 Auto-detected cluster name from Terraform: '{detected_cluster_name}'")
        if detected_cluster_name not in project_identifiers:
            project_identifiers.append(detected_cluster_name)
    
    # 3. Add any user-provided projects
    if args.projects:
        user_projects = [p.strip() for p in args.projects.split(',')]
        project_identifiers.extend(user_projects)
        
    # Remove duplicates
    project_identifiers = list(set(project_identifiers))
    
    print(f"🎯 Targeting resources matching: {project_identifiers}")

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
        cleaner = AWSCleaner(args.region, args.tf_dir, args.state_bucket, args.lock_table, project_identifiers)
        
        bucket_msg = args.state_bucket if args.state_bucket else "NONE (Skipping TF Destroy)"
        print(f"⚠️  WARNING: This will DESTROY all infrastructure in {args.region}.")
        print(f"   Projects: {project_identifiers}")
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
