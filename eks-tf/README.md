## EKS - Cluster Details ##
cluster: eks-np01
Kubernetes version:  1.35
API server endpoint: https://CD1DCF932948EACDC2671A72F686E3E8.gr7.us-east-1.eks.amazonaws.com
OpenID Connect provider URL: https://oidc.eks.us-east-1.amazonaws.com/id/CD1DCF932948EACDC2671A72F686E3E8
Cluster IAM role ARN: arn:aws:iam::744958734165:role/eks-np01-cluster-role
Cluster ARN: arn:aws:eks:us-east-1:744958734165:cluster/eks-np01
Platform version: eks.19

Certificate authority: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURCVENDQWUyZ0F3SUJBZ0lJZFE3blNVZk5YejB3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TlRFeU1qa3dOVEl6TWpSYUZ3MHpOVEV5TWpjd05USTRNalJhTUJVeApFekFSQmdOVkJBTVRDbXQxWW1WeWJtVjBaWE13Z2dFaU1BMEdDU3FHU0liM0RRRUJBUVVBQTRJQkR3QXdnZ0VLCkFvSUJBUUMrZnNPWXM1SEVpekdDdkFJTUR3L0FqZkFGYTVFeW90dXh3VHpOUGEwV2IxeUNyc2hoM1NGVWd4RHoKSU1jMlF2aVhRRTQrUkZPNkJMU2M2SytFcnRVRUFLYUNYSDBtTGQ1M3RvSXJvdTBFeE5nSEtHd3JhTXBxUUw2Ygp6NWkyV0VZMk04N2lQWEFSR0s5QVUrdTZtSUp4a0pCdWFERDVNNHVSSG1ab3lYS2lRTHZEWDBuU1drVncvOVNoCnU2d2hjSGlSNXplUmFYOVNWbHVqSkRVTkdNMlVScHRtYk1HWjBDWmJCWWhUT3AvSTNLN20rQStxUUorR2lJYlUKczRaMlFtNXJBZzl4dmtETDMzTjdFbHdhY291dzNTREVsdndmRjB0OGVvdlF1Mkp4ZTdkc2U1TitySnR2SFJiZwpUN1JnMzBtNnliN3FDU2o4bU1IeHc1SkhjNlQvQWdNQkFBR2pXVEJYTUE0R0ExVWREd0VCL3dRRUF3SUNwREFQCkJnTlZIUk1CQWY4RUJUQURBUUgvTUIwR0ExVWREZ1FXQkJTeTE5WW4zUkVxL3pSMjN4aUM4UEVnTWdKUzF6QVYKQmdOVkhSRUVEakFNZ2dwcmRXSmxjbTVsZEdWek1BMEdDU3FHU0liM0RRRUJDd1VBQTRJQkFRQW5zakJNaHZCbApnL2NnZmlBcjJMb3c3UE5lRCtBUStPR3A5NGJ3bCtIV1VqV05nZGwwdUtLVERsYktGSlRQY016UW1vdDZ5Q1VkCmkvMkFvVGwyVTMxekFPdHJWYUM2UkVTT0xKUC9yRGdaZDlWdnJlREZhRzgzUlpDZExINEZteGorT2dSMnFZNWEKaExPanQrMStyMGxGZHl1OEx5RW9RTE55ckRjY2FOMTk5d1VjbTE2RXl2M1VLcW0wQjhuMGtwdEZ0enJVSDhKegptanBsQW9SRVlwVExiR3NRaXlWMUswd2R5V3JER0RQV2MyZFk2QlcySG9mL3FtaGdpNXB4bnQzc2xtbHZmMyszCkw1V1lWalJZUEgxTVdqTmVKZXY2cnNMRXZFZzVIZ3dYN1VkMmZ2enVDTUFoOVJvVS9JdkJVOU1ZSlRjd3dRUGsKZWNZTXlQdFNxOWJFCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K


Networking
Manage
VPC: vpc-0b5cdc2183b661393 
Cluster IP address family: IPv4
Service IPv4 range: 172.20.0.0/16
Subnets
subnet-0bd74ddf24ebf9730 
subnet-038c7766f3576a8db 
subnet-0d0a8a9146a421f07 
subnet-0258b00a7ba670609 
Cluster security group: sg-0e1ab16f638ccc262 
API server endpoint access: Private
## END ##



## AS: EKS setup on WSL: Install Required Tools in WSL ##

# 1. AWS CLI v2
sudo apt install unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# 2. kubectl (Kubernetes CLI)
curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# 3. eksctl (EKS-specific CLI - simplifies cluster management)
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin/

# 4. helm (optional but recommended for deploying apps)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 5. terraform 
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform -y
terraform --version

Install WSL tools → aws configure → aws sts get-caller-identity
→ eksctl create cluster → aws eks update-kubeconfig → kubectl get nodes


# 6. aws confiure
aws configure
AWS Access Key ID [None]: XXXX
AWS Secret Access Key [None]: XXX
Default region name [None]: us-east-1
Default output format [None]: json

Credentials are stored in ~/.aws/credentials and ~/.aws/config.


# 6. Verify AWS Connection
aws sts get-caller-identity   # confirms your identity + account
aws eks list-clusters          # lists existing EKS clusters

## 7. Connect kubectl to Your EKS Cluster ## 
# Update kubeconfig to point to your EKS cluster
aws eks update-kubeconfig --region us-east-1 --name eks-np01
Added new context arn:aws:eks:us-east-1:744958734165:cluster/eks-np01 to /home/artia/.kube/config

# 8. Verify connection make it provate
kubectl get nodes
artia@hppavilion:~/vscode/git$ kubectl get nodes
E0419 18:10:09.498161  343036 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"https://CD1DCF932948EACDC2671A72F686E3E8.gr7.us-east-1.eks.amazonaws.com/api?timeout=32s\": dial tcp 10.77.18.183:443: i/o timeout"

aws eks update-cluster-config \
  --name eks-np01 \
  --region us-east-1 \
  --resources-vpc-config \
    endpointPublicAccess=true,endpointPrivateAccess=true,publicAccessCidrs="0.0.0.0/0"

# Wait for update to complete (~3-5 mins)
aws eks wait cluster-active --name eks-np01 --region us-east-1

# Then retry
kubectl get nodes
aws eks list-access-entries --cluster-name eks-np01 --region us-east-1


## Step 3: Add Your IAM User to the Cluster
# Get your IAM user ARN
MY_ARN=$(aws sts get-caller-identity --query "Arn" --output text)
echo "My ARN: $MY_ARN"

# Add access entry for your user
aws eks create-access-entry \
  --cluster-name eks-np01 \
  --region us-east-1 \
  --principal-arn $MY_ARN \
  --type STANDARD

# Associate admin policy to your user
aws eks associate-access-policy \
  --cluster-name eks-np01 \
  --region us-east-1 \
  --principal-arn $MY_ARN \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster


# 9. Refresh kubeconfig & Test
aws eks update-kubeconfig --region us-east-1 --name eks-np01
kubectl get nodes


# 10. get all eks cluster details  Save everything to a file for easy reference
aws eks describe-cluster --name eks-np01 --region us-east-1 \
  --output json > eks-np01-config.json

cat eks-np01-config.json


artia@hppavilion:~/vscode/git/python_labs/AIML$ aws eks list-access-entries --cluster-name eks-np01 --region us-east-1
{
    "accessEntries": [
        "arn:aws:iam::744958734165:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_2025_hilabs_devops_sso_access_700e0285e5e2edb1",
        "arn:aws:iam::744958734165:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_4165_AdministratorAccess_d8588457fd2f41bb",
        "arn:aws:iam::744958734165:role/aws-service-role/eks.amazonaws.com/AWSServiceRoleForAmazonEKS",
        "arn:aws:iam::744958734165:role/eks-np01-bootstrap-node-role",
        "arn:aws:iam::744958734165:role/eks-np01-cluster-admin-role",
        "arn:aws:iam::744958734165:role/eks-np01-kubectl-jump-role",
        "arn:aws:iam::744958734165:user/hilabs-svc-acc"
    ]
}

artia@hppavilion:~/vscode/git/python_labs/AIML$ aws eks list-nodegroups --cluster-name eks-np01 --region us-east-1
{
    "nodegroups": [
        "eks-np01-bootstrap"
    ]
}
artia@hppavilion:~/vscode/git/python_labs/AIML$ 


# Describe each node group - save this output!
aws eks describe-nodegroup \
  --cluster-name eks-np01 \
  --region us-east-1 \
  --nodegroup-name eks-np01-bootstrap --output json > nodegroup-backup.json



# Section 2: Create Complete Terraform Config
mkdir eks-tf && cd eks-tf
touch main.tf variables.tf outputs.tf providers.tf

cd eks-tf

# terraform init
facigng issue with installing hashiorp/aws provider

artia@hppavilion:~/vscode/git/python_labs/eks-tf$ terraform init
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.100.0...
╷
│ Error: Failed to install provider
│ 
│ Error while installing hashicorp/aws v5.100.0: releases.hashicorp.com: local error: tls: bad record MAC

mostlikely fixed by "sudo ethtool -K eth0 tx off rx off"
mostly due to wsl with wiregard on

# to make it permanent add to wsl.conf or ~/.bashrc
bash# Add to WSL boot config
sudo tee /etc/wsl.conf << 'EOF'
[boot]
command = ethtool -K eth0 tx off rx off
EOF

echo 'sudo ethtool -K eth0 tx off rx off 2>/dev/null' >> ~/.bashrc

# run plan
terraform plan
terraform plan -out=eks-np01.tfplan  #binary file
terraform show eks-np01.tfplan > eks-np01-plan.txt
terraform plan 2>&1 | tee eks-np01-plan.txt

# Export plan as JSON
terraform plan -out=eks-np01.tfplan
terraform show -json eks-np01.tfplan > eks-np01-plan.json

# Pretty print it
terraform show -json eks-np01.tfplan | python3 -m json.tool > eks-np01-plan-pp.json

# Import cluster
terraform import aws_eks_cluster.eks_np01 eks-np01
artia@hppavilion:~/vscode/git/python_labs/eks-tf$ terraform import aws_eks_cluster.eks_np01 eks-np01
aws_eks_cluster.eks_np01: Importing from ID "eks-np01"...
data.aws_caller_identity.current: Reading...
aws_eks_cluster.eks_np01: Import prepared!
  Prepared aws_eks_cluster for import
aws_eks_cluster.eks_np01: Refreshing state... [id=eks-np01]
data.aws_caller_identity.current: Read complete after 0s [id=744958734165]

Import successful!

The resources that were imported are shown above. These resources are now in
your Terraform state and will henceforth be managed by Terraform.

artia@hppavilion:~/vscode/git/python_labs/eks-tf$ 

# Import node group
terraform import aws_eks_node_group.bootstrap eks-np01:eks-np01-bootstrap
artia@hppavilion:~/vscode/git/python_labs/eks-tf$ terraform import aws_eks_node_group.bootstrap eks-np01:eks-np01-bootstrap
data.aws_caller_identity.current: Reading...
aws_eks_node_group.bootstrap: Importing from ID "eks-np01:eks-np01-bootstrap"...
aws_eks_node_group.bootstrap: Import prepared!
  Prepared aws_eks_node_group for import
aws_eks_node_group.bootstrap: Refreshing state... [id=eks-np01:eks-np01-bootstrap]
data.aws_caller_identity.current: Read complete after 1s [id=744958734165]

Import successful!

The resources that were imported are shown above. These resources are now in
your Terraform state and will henceforth be managed by Terraform.

artia@hppavilion:~/vscode/git/python_labs/eks-tf$ 

# inport access entry
artia@hppavilion:~/vscode/git/python_labs/eks-tf$ terraform import aws_eks_access_entry.admin arn:aws:eks:us-east-1:744958734165:access-entry/eks-np01/user/744958734165/hilabs-svc-acc
data.aws_caller_identity.current: Reading...
data.aws_caller_identity.current: Read complete after 0s [id=744958734165]
aws_eks_access_entry.admin: Importing from ID "arn:aws:eks:us-east-1:744958734165:access-entry/eks-np01/user/744958734165/hilabs-svc-acc"...
aws_eks_access_entry.admin: Import prepared!
  Prepared aws_eks_access_entry for import
aws_eks_access_entry.admin: Refreshing state... [id=arn:aws:eks:us-east-1:744958734165:access-entry/eks-np01/user/744958734165/hilabs-svc-acc]
╷
│ Error: reading EKS Access Entry (arn:aws:eks:us-east-1:744958734165:access-entry/eks-np01/user/744958734165/hilabs-svc-acc): operation error EKS: DescribeAccessEntry, https response error StatusCode: 400, RequestID: d2e4ed4f-bea6-4f48-9ea7-1cf2e20f5857, api error InvalidParameterException: The principalArn parameter format is not valid
│ 
│ 
╵

NOT fixing so fianlly deleted
aws eks delete-access-entry \
  --cluster-name eks-np01 \
  --principal-arn arn:aws:iam::744958734165:user/hilabs-svc-acc \
  --region us-east-1


# Check drift — fix anything until you see "No changes"
terraform plan
terraform plan -out=eks-np01_afterimport.tfplan  #binary file
terraform show eks-np01_afterimport.tfplan > eks-np01-plan_afterimport.txt
terraform plan 2>&1 | tee eks-np01-plan_afterimport.txt


terraform plan -out=eks-np01_afterimport.tfplan
terraform show -json eks-np01_afterimport.tfplan > eks-np01-plan_afterimport.json


terraform show -json eks-np01_afterimport.tfplan | python3 -m json.tool > eks-np01-plan-pp_afterimport.json

# Once plan is clean — safe to make changes
terraform apply


# daily tear down
    # End of learning session
terraform destroy -auto-approve

    # Start of next learning session  
terraform apply -auto-approve
aws eks update-kubeconfig --region us-east-1 --name eks-np01
kubectl get nodes

~/.bashrc
alias eks-up='cd ~/vscode/git/python_labs/eks-tf && terraform apply -auto-approve'
alias eks-down='cd ~/vscode/git/python_labs/eks-tf && terraform destroy -auto-approve'




day1 status
✅ EKS cluster eks-np01        — imported + managed by TF
✅ Remote state in S3           — survives destroy/recreate  
✅ OIDC provider                — IRSA enabled
✅ EBS CSI addon + IAM role     — pods running
✅ VPC CNI + CoreDNS            — networking working
✅ Pod Identity agent           — running
✅ Access entry (hilabs-svc-acc) — kubectl working
✅ Node group (t3.medium)       — public subnet, nodes joining
✅ terraform plan = No changes  — clean state

CREATE S3 BUCKET & DYNAMODB
./create_s3_bucket_dynamodb.sh


# This moves your local state to S3
Add backend.tf file
terraform init -migrate-state


# Check state file exists in S3
aws s3 ls s3://eks-np01-tfstate-744958734165/eks-np01/

# Verify Terraform uses remote state
terraform state list

# Confirm no local state file remains
ls -la terraform.tfstate 2>/dev/null || echo "✅ No local state - all in S3!"


# Commit current state to git
cd ~/vscode/git/python_labs/eks-tf
git add -A
git commit -m "M1+M2 complete: cluster imported, addons working, IRSA configured"
git push

# Also scale down nodes to save cost
aws eks update-nodegroup-config \
  --cluster-name eks-np01 \
  --nodegroup-name eks-np01-bootstrap \
  --scaling-config minSize=0,maxSize=2,desiredSize=0 \
  --region us-east-1

echo "Nodes scaled to 0 - saving cost!"





# Ready for Phase 2 — M3: RBAC + Namespaces
When you're ready just say "start M3" and we'll build:
rbac.tf      — namespaces, roles, rolebindings
configmaps.tf — app configs, feature flags
calico.tf    — network policies

touch rbac.tf configmaps.tf calico.tf kyverno.tf
terraform init -upgrade

# Save and apply
terraform plan -out=m3.tfplan
terraform apply m3.tfplan

# Check namespaces
kubectl get namespaces

# Check cluster roles
kubectl get clusterroles | grep eks-

# Check role bindings in app namespace
kubectl get rolebindings -n app

# Check configmaps
kubectl get configmaps -n app

# Check service account
kubectl get sa -n app



# M4 install kyverno, then add policies
add kyverno.tf
add providers like helm in providers.tf

terraform init -upgrade # use when there is change in version for providers
terraform plan

terraform init -reconfigure # changign backend use lock file instead dynamodb

# Apply only kyverno helm release first - install / upgrade kyverno so that its availble for rest all poliicies
terraform apply -target=helm_release.kyverno
watch kubectl get pods -n kyverno
Wait until all 4 pods show Running then run:



terraform plan -out=m4.tfplan
terraform apply m4.tfplan
watch kubectl get pods -n kyverno


# See all available chart versions
helm repo add kyverno https://kyverno.github.io/kyverno
helm repo update
helm search repo kyverno/kyverno --versions | head -20




# Browse official policy library
helm repo add kyverno-policies https://kyverno.github.io/kyverno
helm repo update
helm search repo kyverno-policies/kyverno --versions | head -20

terraform plan -target=helm_release.kyverno_policies
terraform apply -target=helm_release.kyverno_policies

# Verify policies installed
kubectl get clusterpolicies | head -30

# Check cluster-wide violations
kubectl get clusterpolicyreport -A

# Check namespace violations
kubectl get policyreport -n app

# Detailed violation report
kubectl describe clusterpolicyreport | grep -A5 "fail"

# Count violations per policy
kubectl get clusterpolicyreport -o json | \
  python3 -m json.tool | \
  grep "policy\|result" | head -40