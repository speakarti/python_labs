# EKS Platform Setup — Complete Documentation

**Date:** April 20, 2026  
**Cluster:** eks-np01  
**Region:** us-east-1  
**Account:** 744958734165  
**Author:** hilabs-svc-acc  

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites & Tools](#prerequisites--tools)
3. [Phase 1 — Foundation](#phase-1--foundation)
   - [Remote State (S3 + S3 Native Locking)](#remote-state-s3--s3-native-locking)
   - [Terraform Providers](#terraform-providers)
   - [EKS Cluster Import](#eks-cluster-import)
   - [Core EKS Addons](#core-eks-addons)
   - [IRSA — IAM Roles for Service Accounts](#irsa--iam-roles-for-service-accounts)
4. [Phase 2 — Security Baseline](#phase-2--security-baseline)
   - [RBAC + Namespaces](#rbac--namespaces)
   - [ConfigMaps](#configmaps)
   - [Kyverno Policy Engine](#kyverno-policy-engine)
5. [Networking Architecture](#networking-architecture)
6. [Node Group Configuration](#node-group-configuration)
7. [Troubleshooting Log](#troubleshooting-log)
8. [Cost Saving Strategy](#cost-saving-strategy)
9. [File Structure](#file-structure)
10. [Next Steps](#next-steps)

---

## Overview

This document describes the complete setup of an AWS EKS (Elastic Kubernetes Service) cluster managed by Terraform, including all infrastructure decisions, troubleshooting steps, and lessons learned.

### Architecture Summary

```
AWS Account (744958734165)
└── VPC (vpc-0b5cdc2183b661393) — 10.77.0.0/16
    ├── Public Subnets (IGW route)
    │   ├── subnet-0d0a8a9146a421f07 (us-east-1b)
    │   └── subnet-0258b00a7ba670609 (us-east-1a)
    ├── Private Subnets (TGW route — hub-spoke)
    │   ├── subnet-0bd74ddf24ebf9730 (us-east-1b)
    │   └── subnet-038c7766f3576a8db (us-east-1a)
    └── EKS Cluster (eks-np01)
        ├── Control Plane (managed by AWS)
        └── Node Group (eks-np01-bootstrap)
            └── t3.medium (public subnet)
```

### Technology Stack

| Category | Tools |
|----------|-------|
| IaC | Terraform v1.14.8 |
| Cloud | AWS EKS v1.35 |
| Container Runtime | containerd (AL2023) |
| Node Management | Managed Node Groups |
| Policy Engine | Kyverno v3.7.1 |
| State Backend | S3 + S3 Native Locking (`use_lockfile`) |
| OS | WSL2 (Ubuntu) on Windows |

---

## Prerequisites & Tools

### Tools Installed

```bash
# AWS CLI v2
aws --version

# kubectl
kubectl version --client

# Terraform
terraform version

# Helm
helm version
```

### WSL2 Network Fix

A critical fix was required for Terraform provider downloads in WSL2. The Hyper-V virtual NIC has a checksum offload bug that causes large file downloads to hang or fail with TLS errors.

```bash
# Fix — disable checksum offloading
sudo ethtool -K eth0 tx off rx off

# Make permanent in /etc/wsl.conf
sudo tee /etc/wsl.conf << 'EOF'
[boot]
command = ethtool -K eth0 tx off rx off
EOF
```

**Why this happens:** WSL2 uses a Hyper-V virtual NIC that claims to handle TCP checksums (offload) but computes them incorrectly for large packets. This causes TLS record MAC errors and download hangs specifically for Go-based tools (Terraform, kubectl, helm) that use larger TCP segments than curl.

### AWS Configuration

```bash
aws configure
# AWS Access Key ID: [from IAM]
# AWS Secret Access Key: [from IAM]
# Default region: us-east-1
# Output format: json
```

---

## Phase 1 — Foundation

### Remote State (S3 + S3 Native Locking)

**File:** `backend.tf`

```hcl
terraform {
  backend "s3" {
    bucket       = "eks-np01-tfstate-744958734165"
    key          = "eks-np01/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true   # S3 native locking — no DynamoDB needed
    encrypt      = true
  }
}
```

**Why:** Terraform state must be stored remotely for:

| Reason | Explanation |
|--------|-------------|
| Persistence | State survives laptop loss, WSL reset, disk failure |
| Team collaboration | Multiple engineers can run Terraform safely |
| State locking | Prevents simultaneous applies causing state corruption |
| Versioning | S3 versioning allows rollback to previous state |
| Destroy/recreate | Cluster can be destroyed and recreated without losing state |

**Resources created:**

```bash
# S3 bucket with versioning + encryption + public access blocked
aws s3 mb s3://eks-np01-tfstate-744958734165
aws s3api put-bucket-versioning \
  --bucket eks-np01-tfstate-744958734165 \
  --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption \
  --bucket eks-np01-tfstate-744958734165 \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
```

#### State Locking Evolution

Terraform historically used DynamoDB for state locking. As of **Terraform v1.10+**, native S3 locking is available using S3 object locks — no DynamoDB required.

| Method | Terraform Version | Parameter | Extra Resource |
|--------|------------------|-----------|---------------|
| DynamoDB locking | < v1.10 | `dynamodb_table = "table-name"` | DynamoDB table required |
| S3 native locking | >= v1.10 | `use_lockfile = true` | None — uses same S3 bucket |

**How S3 native locking works:**

```
terraform apply starts
        ↓
Creates lock file in S3:
  eks-np01/terraform.tfstate.tflock
        ↓
Apply runs safely
        ↓
Lock file deleted on completion

If another engineer runs apply simultaneously:
        ↓
Sees lock file exists → errors:
  "Error: state file is locked"
        ↓
Must wait for first apply to finish
```

**We started with `dynamodb_table` and migrated to `use_lockfile`** after Terraform showed this deprecation warning:

```
Warning: The parameter "dynamodb_table" is deprecated.
Use parameter "use_lockfile" instead.
```

The DynamoDB table (`eks-np01-tf-lock`) was created initially but is no longer used and can be safely deleted:

```bash
aws dynamodb delete-table \
  --table-name eks-np01-tf-lock \
  --region us-east-1
```

#### Migrating from Local State to S3 Backend

When you first add a backend configuration to an existing project that has local state, use `-migrate-state` to move the existing state to S3:

```bash
# Add backend.tf with S3 config, then run:
terraform init -migrate-state

# Terraform will ask:
# "Do you want to copy existing state to the new backend? yes"
# Type yes — this moves local terraform.tfstate to S3

# Verify state is now in S3
aws s3 ls s3://eks-np01-tfstate-744958734165/eks-np01/

# Verify no local state remains
ls terraform.tfstate 2>/dev/null || echo "No local state — all in S3!"
```

**Why `-migrate-state` not just `-reconfigure`:**

| Flag | When to use |
|------|-------------|
| `-migrate-state` | Moving state FROM one backend TO another (local → S3, S3 → S3) |
| `-reconfigure` | Changing backend config without moving state (e.g. changing bucket name) |
| `-upgrade` | Updating provider versions in lock file |

---

### Terraform Providers

**File:** `providers.tf`

```hcl
terraform {
  required_providers {
    aws        = { source = "hashicorp/aws",        version = "~> 5.82" }
    tls        = { source = "hashicorp/tls",        version = "~> 4.0"  }
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 3.1"  }
    helm       = { source = "hashicorp/helm",       version = "~> 2.12" }
  }
}
```

| Provider | Purpose |
|----------|---------|
| `aws` | Manages all AWS resources (EKS, IAM, EC2, VPC) |
| `tls` | Fetches TLS certificate fingerprint for OIDC provider |
| `kubernetes` | Creates K8s resources (namespaces, RBAC, configmaps) |
| `helm` | Installs Helm charts (Kyverno, monitoring, etc.) |

**Both `kubernetes` and `helm` providers use `exec` auth:**

```hcl
exec {
  api_version = "client.authentication.k8s.io/v1beta1"
  args        = ["eks", "get-token", "--cluster-name", var.cluster_name]
  command     = "aws"
}
```

This uses the AWS CLI to generate a short-lived token for authenticating to the cluster, avoiding static kubeconfig credentials.

---

### EKS Cluster Import

The cluster `eks-np01` was **pre-existing** (created manually). It was imported into Terraform state rather than recreated, preserving all networking and configuration.

```bash
# Import cluster
terraform import aws_eks_cluster.eks_np01 eks-np01

# Import node group
terraform import aws_eks_node_group.bootstrap eks-np01:eks-np01-bootstrap
```

**Key cluster configuration:**

```hcl
resource "aws_eks_cluster" "eks_np01" {
  name                          = "eks-np01"
  version                       = "1.35"
  role_arn                      = "arn:aws:iam::744958734165:role/eks-np01-cluster-role"
  bootstrap_self_managed_addons = false  # critical — prevents destroy/recreate

  vpc_config {
    subnet_ids              = [all 4 subnets]
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
  }

  access_config {
    authentication_mode = "API"  # modern auth, no aws-auth ConfigMap needed
  }
}
```

**`bootstrap_self_managed_addons = false`** — this was a critical fix. The existing cluster had this set to `false` but Terraform's default is `true`. Without explicitly setting it, Terraform would destroy and recreate the cluster on every apply.

### Cluster Access Entry

```hcl
resource "aws_eks_access_entry" "admins" {
  for_each      = toset(var.cluster_admin_arns)
  cluster_name  = aws_eks_cluster.eks_np01.name
  principal_arn = each.value
  type          = "STANDARD"
}

resource "aws_eks_access_policy_association" "admins" {
  for_each      = toset(var.cluster_admin_arns)
  cluster_name  = aws_eks_cluster.eks_np01.name
  principal_arn = each.value
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
  access_scope { type = "cluster" }
}
```

**Why managed in Terraform:** Without this in TF, every `terraform destroy` + `terraform apply` cycle would require manually re-adding access, breaking `kubectl` every time.

---

### Core EKS Addons

**File:** `addons.tf`

```hcl
resource "aws_eks_addon" "vpc_cni"      { addon_name = "vpc-cni" }
resource "aws_eks_addon" "coredns"      { addon_name = "coredns" }
resource "aws_eks_addon" "kube_proxy"   { addon_name = "kube-proxy" }
resource "aws_eks_addon" "ebs_csi"      { addon_name = "aws-ebs-csi-driver" }
resource "aws_eks_addon" "pod_identity" { addon_name = "eks-pod-identity-agent" }
```

| Addon | Purpose | Why Required |
|-------|---------|--------------|
| `vpc-cni` | AWS VPC networking for pods | Pods get VPC IPs, enabling direct VPC routing |
| `coredns` | DNS resolution inside cluster | Service discovery — pods find each other by name |
| `kube-proxy` | Network rules on each node | Enables Service IP routing via iptables/ipvs |
| `aws-ebs-csi-driver` | EBS volume provisioning | PersistentVolumes for stateful apps (databases etc.) |
| `eks-pod-identity-agent` | Pod identity for IRSA | Enables pods to assume IAM roles securely |

---

### IRSA — IAM Roles for Service Accounts

**File:** `iam.tf`

IRSA (IAM Roles for Service Accounts) is the secure way for Kubernetes pods to access AWS services without static credentials.

#### OIDC Provider

```hcl
data "tls_certificate" "eks" {
  url = aws_eks_cluster.eks_np01.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.eks_np01.identity[0].oidc[0].issuer
}
```

**Why:** Registers the EKS cluster as a trusted identity provider in AWS IAM. Without this, AWS has no way to trust tokens issued by Kubernetes service accounts.

#### EBS CSI IAM Role

```hcl
resource "aws_iam_role" "ebs_csi" {
  name               = "eks-np01-ebs-csi-role"
  assume_role_policy = data.aws_iam_policy_document.ebs_csi_assume.json
}

resource "aws_iam_role_policy_attachment" "ebs_csi" {
  role       = aws_iam_role.ebs_csi.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}
```

**Trust policy restricts to exactly one service account:**

```hcl
condition {
  test     = "StringEquals"
  variable = "${oidc_url}:sub"
  values   = ["system:serviceaccount:kube-system:ebs-csi-controller-sa"]
}
```

**Why IRSA instead of node IAM role:**

```
Node IAM role (bad):
  ALL pods share the node role
  EBS CSI permissions available to every pod
  Blast radius = entire node

IRSA (good):
  EBS CSI pod gets ONLY EBS permissions
  Your app pod gets ONLY S3 permissions
  Blast radius = one pod
```

#### IRSA Flow

```
Pod starts with ServiceAccount annotation (role ARN)
        ↓
EKS Pod Identity Webhook injects AWS token
        ↓
Pod calls STS AssumeRoleWithWebIdentity
        ↓
AWS verifies OIDC token + trust policy conditions
        ↓
AWS returns temporary credentials (valid 1 hour)
        ↓
Pod uses credentials to call AWS APIs
```

---

## Phase 2 — Security Baseline

### RBAC + Namespaces

**File:** `rbac.tf`

#### Namespaces

```hcl
resource "kubernetes_namespace_v1" "namespaces" {
  for_each = toset([
    "app", "monitoring", "istio-system", "karpenter",
    "vault", "kafka", "cert-manager", "argocd", "kyverno"
  ])
}
```

**Why separate namespaces:**

| Namespace | Purpose | Isolation Benefit |
|-----------|---------|-------------------|
| `app` | Application workloads | Separate from system components |
| `monitoring` | Prometheus, Grafana, Loki | Observability stack isolated |
| `istio-system` | Service mesh control plane | Mesh components separated |
| `karpenter` | Node autoscaler | Cluster management isolated |
| `vault` | Secrets management | High-security isolation |
| `kafka` | Message streaming | Data plane separated |
| `cert-manager` | TLS certificate management | PKI isolated |
| `argocd` | GitOps controller | Deployment pipeline isolated |
| `kyverno` | Policy engine | Security controls isolated |

#### ClusterRoles

```hcl
# Read-only: view pods, services, configmaps
resource "kubernetes_cluster_role_v1" "readonly" { ... }

# Developer: CRUD on pods, deployments, services + log access
resource "kubernetes_cluster_role_v1" "developer" { ... }

# Admin: full access to everything
resource "kubernetes_cluster_role_v1" "admin" { ... }
```

**Why three tiers:**

```
readonly  → monitoring teams, auditors, on-call viewers
developer → application teams, can deploy and debug
admin     → platform engineers, SREs, break-glass access
```

**Principle of Least Privilege** — users only get the minimum permissions needed for their role, limiting blast radius of compromised credentials.

#### RoleBindings

```hcl
# Bind developer role to "developers" group in app namespace only
resource "kubernetes_role_binding_v1" "app_developer" {
  subject {
    kind = "Group"
    name = "developers"
  }
}
```

Bindings use **Groups** not individual users — when a developer joins/leaves, only the group membership changes, not the Kubernetes RBAC config.

---

### ConfigMaps

**File:** `configmaps.tf`

```hcl
resource "kubernetes_config_map_v1" "app_config" {
  data = {
    APP_ENV      = var.environment
    REGION       = var.region
    CLUSTER_NAME = var.cluster_name
    LOG_LEVEL    = "info"
  }
}

resource "kubernetes_config_map_v1" "feature_flags" {
  data = {
    ENABLE_NEW_UI    = "false"
    ENABLE_DARK_MODE = "true"
    MAINTENANCE_MODE = "false"
  }
}
```

**Why ConfigMaps in Terraform:**

| Approach | Problem |
|----------|---------|
| Hardcode in app container | Rebuilding image just to change config |
| ConfigMap via kubectl | Not tracked, lost on cluster recreate |
| **ConfigMap via Terraform** | Version controlled, recreated automatically ✅ |

ConfigMaps allow environment-specific configuration without rebuilding container images. Feature flags enable runtime behaviour changes without deployments.

---

### Kyverno Policy Engine

**File:** `kyverno.tf`

Kyverno is a Kubernetes-native policy engine that acts as an admission controller — every pod creation/update request passes through Kyverno before being accepted.

#### Installation

```hcl
resource "helm_release" "kyverno" {
  name       = "kyverno"
  repository = "https://kyverno.github.io/kyverno"
  chart      = "kyverno"
  version    = "3.7.1"
  namespace  = "kyverno"
}
```

**Kyverno components installed:**

| Component | Role |
|-----------|------|
| Admission Controller | Validates/mutates resources at creation time |
| Background Controller | Scans existing resources for policy violations |
| Cleanup Controller | Handles TTL-based resource cleanup |
| Reports Controller | Generates policy compliance reports |

#### CIS Benchmark Policy Library

```hcl
resource "helm_release" "kyverno_policies" {
  name    = "kyverno-policies"
  chart   = "kyverno-policies"
  version = "3.7.1"

  set { name = "podSecurityStandard";      value = "baseline" }
  set { name = "validationFailureAction";  value = "Audit"    }
}
```

**Policies installed by baseline standard:**

| Policy | Blocks |
|--------|--------|
| `disallow-privileged-containers` | `privileged: true` containers |
| `disallow-host-namespaces` | `hostNetwork`, `hostPID`, `hostIPC` |
| `disallow-host-path` | Direct host filesystem mounts |
| `disallow-host-ports` | `hostPort` usage |
| `restrict-volume-types` | Dangerous volume types |
| `restrict-sysctls` | Unsafe kernel parameters |
| `disallow-capabilities` | Dangerous Linux capabilities |
| `restrict-apparmor-profiles` | Custom AppArmor profiles |
| `disallow-seccomp` | Unconfined seccomp profiles |

#### Custom Policies

```hcl
# Require CPU and memory limits on all pods
policy_require_limits

# Block :latest image tags
policy_disallow_latest

# Require app/env/team labels on app namespace pods
policy_require_labels

# Block privileged containers
policy_no_privileged

# Auto-add managed-by and cluster labels (mutation)
policy_add_labels
```

**Audit vs Enforce mode:**

```
Audit  → logs violations, does NOT block pods (safe to start with)
Enforce → blocks non-compliant pods at creation time

Recommended workflow:
  Week 1-2: Audit — review violations
  Week 3+:  Enforce — block violations
```

**Check violations:**

```bash
kubectl get clusterpolicyreport -A
kubectl get policyreport -n app
```

---

## Networking Architecture

### Hub-Spoke with Transit Gateway

The VPC uses a hub-spoke architecture via AWS Transit Gateway (TGW):

```
Your VPC (10.77.0.0/16)
  Private subnets → 0.0.0.0/0 → tgw-0bcc6f98fa3e2aa51
                                        ↓
                              Hub VPC (central egress)
                                        ↓
                                    Internet

  Public subnets  → 0.0.0.0/0 → igw-05cc7bfd5f53848f7
                                        ↓
                                    Internet (direct)
```

### Subnet Layout

| Subnet | CIDR | AZ | Type | Route |
|--------|------|----|------|-------|
| subnet-0d0a8a9146a421f07 | 10.77.16.0/20 | us-east-1b | Public | IGW |
| subnet-0258b00a7ba670609 | 10.77.0.0/20 | us-east-1a | Public | IGW |
| subnet-0bd74ddf24ebf9730 | 10.77.80.0/20 | us-east-1b | Private | TGW |
| subnet-038c7766f3576a8db | 10.77.64.0/20 | us-east-1a | Private | TGW |

### TGW Issue Discovered

The TGW attachment for this VPC is associated with route table `tgw-rtb-06158adb9319962c6` which only has one route (`10.30.0.0/16`) — no default route (`0.0.0.0/0`). This means nodes in private subnets cannot reach AWS APIs, causing bootstrap failures.

**Root cause:** Hub-spoke TGW route table association is missing the default route to the hub. This is a network team configuration issue, not an application issue.

**Current workaround:** Node group uses public subnets (direct IGW) until network team fixes the TGW route table.

**Proper fix (requires network team):**
```bash
aws ec2 create-transit-gateway-route \
  --transit-gateway-route-table-id tgw-rtb-06158adb9319962c6 \
  --destination-cidr-block 0.0.0.0/0 \
  --transit-gateway-attachment-id <HUB_ATTACHMENT_ID>
```

---

## Node Group Configuration

**File:** `main.tf`

```hcl
resource "aws_eks_node_group" "bootstrap" {
  cluster_name    = aws_eks_cluster.eks_np01.name
  node_group_name = "eks-np01-bootstrap"
  node_role_arn   = "arn:aws:iam::744958734165:role/eks-np01-bootstrap-node-role"
  version         = "1.35"

  subnet_ids = [
    "subnet-0d0a8a9146a421f07",  # public — IGW route
    "subnet-0258b00a7ba670609"   # public — IGW route
  ]

  ami_type       = "AL2023_x86_64_STANDARD"
  instance_types = ["t3.medium"]
  disk_size      = 20

  scaling_config {
    min_size     = 0   # scale to 0 to save cost
    max_size     = 2
    desired_size = 1
  }
}
```

### Instance Type Selection

| Instance | vCPU | RAM | Use Case |
|----------|------|-----|---------|
| t3.micro | 2 | 1GB | ❌ Too small — system pods use all 4 pod slots |
| t3.small | 2 | 2GB | ⚠️ Bare minimum |
| **t3.medium** | **2** | **4GB** | ✅ Recommended minimum for EKS |
| t3.large | 2 | 8GB | ✅ Production workloads |

`t3.micro` was the original instance type and caused node failure — EKS system pods (aws-node, coredns, kube-proxy, ebs-csi-node, eks-pod-identity) consume all 4 available pod slots on `t3.micro`, leaving zero for application workloads.

### Node IAM Role Policies

| Policy | Why Required |
|--------|-------------|
| `AmazonEKSWorkerNodePolicy` | Core EKS node registration |
| `AmazonEKS_CNI_Policy` | VPC CNI networking |
| `AmazonEC2ContainerRegistryReadOnly` | Pull images from ECR |
| `AmazonSSMManagedInstanceCore` | SSM Session Manager access (no SSH needed) |

### Bootstrap Taint

The original node group had a `bootstrap=true:NoSchedule` taint. This was inherited from the original cluster setup and prevented system pods (CoreDNS, EBS CSI controller) from scheduling since they are Deployments without this toleration (unlike DaemonSets which tolerate all taints automatically).

**DaemonSets vs Deployments and taints:**

```
DaemonSet pods (aws-node, kube-proxy, ebs-csi-node):
  Automatically get toleration: operator: Exists
  → Schedule on ANY node regardless of taints ✅

Deployment pods (coredns, ebs-csi-controller):
  Only tolerate explicitly listed taints
  → Cannot schedule on bootstrap-tainted node ❌
```

---

## Troubleshooting Log

### Issue 1: kubectl Connection Timeout
**Symptom:** `dial tcp 10.77.18.183:443: i/o timeout`  
**Cause:** Cluster endpoint was private-only — no public access  
**Fix:** `aws eks update-cluster-config --resources-vpc-config endpointPublicAccess=true`

### Issue 2: `the server has asked for the client to provide credentials`
**Symptom:** kubectl authentication failure after enabling public access  
**Cause:** IAM user `hilabs-svc-acc` not in cluster access entries  
**Fix:** `aws eks create-access-entry` + `associate-access-policy`

### Issue 3: Terraform Provider Download Hanging
**Symptom:** `terraform init` hangs indefinitely on provider download  
**Cause:** WSL2 Hyper-V virtual NIC checksum offload bug corrupts large TCP segments  
**Fix:** `sudo ethtool -K eth0 tx off rx off`

### Issue 4: Node `NodeCreationFailure`
**Symptom:** Node group fails with `Instances failed to join the kubernetes cluster`  
**Root cause:** `nodeadm` bootstrap retrying `EC2/DescribeInstances` 9+ times and timing out  
**Cause:** Private subnets route to TGW but TGW route table has no `0.0.0.0/0` → packets dropped  
**Fix:** Move node group to public subnets (IGW direct route)

### Issue 5: EBS CSI Controller CrashLoopBackOff
**Symptom:** `no EC2 IMDS role found, get credentials: failed to refresh cached credentials`  
**Cause:** EBS CSI addon had no `service_account_role_arn` — falling back to IMDS which is inaccessible from pods  
**Fix:** Create OIDC provider + IAM role + attach to addon via `service_account_role_arn`

### Issue 6: ASG Lifecycle Hook Blocking Node Deletion
**Symptom:** Node group deletion stuck at `Terminating:Wait` for 30+ minutes  
**Cause:** `Terminate-LC-Hook` lifecycle hook sending SNS to external account `886005959465` — external system not completing the hook  
**Fix:** Waited for 30-minute `HeartbeatTimeout` to auto-complete with `DefaultResult: CONTINUE`

### Issue 7: Kyverno Image Pull Error
**Symptom:** `Failed to pull image "bitnami/kubectl:1.28.5": not found`  
**Cause:** Kyverno chart `3.1.4` cleanup controller references a non-existent bitnami image tag  
**Fix:** Upgraded to Kyverno chart `3.7.1` which uses correct image references

### Issue 8: Kyverno Policy Conflict
**Symptom:** `ClusterPolicy "disallow-privileged-containers" exists and cannot be imported`  
**Cause:** Custom `disallow-privileged-containers` policy from manual Terraform resource conflicts with `kyverno-policies` Helm chart installing the same policy  
**Fix:** Remove duplicate custom policy — rely on `kyverno-policies` library instead

---

## Cost Saving Strategy

### Cost Breakdown

| Resource | Cost/hour | Cost/day | Notes |
|----------|-----------|---------|-------|
| EKS Control Plane | $0.10 | $2.40 | Always running |
| t3.medium node | $0.0416 | $1.00 | Per node |
| EBS 20GB | ~$0.002 | $0.05 | Per node |
| **Total running** | | **~$3.46** | |
| **Nodes scaled to 0** | | **~$2.40** | Only control plane |

### Scale Down When Not Using

```bash
# Add to ~/.bashrc
alias eks-up='aws eks update-nodegroup-config \
  --cluster-name eks-np01 \
  --nodegroup-name eks-np01-bootstrap \
  --scaling-config minSize=1,maxSize=2,desiredSize=1 \
  --region us-east-1'

alias eks-down='aws eks update-nodegroup-config \
  --cluster-name eks-np01 \
  --nodegroup-name eks-np01-bootstrap \
  --scaling-config minSize=0,maxSize=2,desiredSize=0 \
  --region us-east-1'

alias eks-status='kubectl get nodes && kubectl get pods -A'
alias eks-connect='aws eks update-kubeconfig --region us-east-1 --name eks-np01'
```

### Monthly Cost Estimate

| Strategy | Monthly Cost |
|----------|-------------|
| Always on | ~$104 |
| Scale to 0 at night (16hrs off) | ~$36 |
| Destroy daily | ~$0 (15 min recreate time) |

---

## File Structure

```
eks-tf/
├── backend.tf          # S3 remote state configuration
├── providers.tf        # AWS, Kubernetes, Helm, TLS providers
├── variables.tf        # Input variables (cluster_name, region, environment)
├── outputs.tf          # Cluster ARN, endpoint, OIDC issuer
├── main.tf             # EKS cluster + node group + access entries
├── addons.tf           # Core EKS managed addons
├── iam.tf              # OIDC provider + IRSA roles (EBS CSI)
├── rbac.tf             # Namespaces + ClusterRoles + RoleBindings + ServiceAccounts
├── configmaps.tf       # App config + feature flags
├── kyverno.tf          # Kyverno engine + CIS policies + custom policies
└── .gitignore          # Excludes .terraform/, *.tfstate, *.tfplan
```

### Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `cluster_name` | `eks-np01` | EKS cluster name |
| `region` | `us-east-1` | AWS region |
| `account_id` | `744958734165` | AWS account ID |
| `environment` | `nonprod` | Environment label |
| `cluster_admin_arns` | `[hilabs-svc-acc]` | IAM ARNs for cluster admin access |

---

## Next Steps

### Phase 2 Remaining (M4 → M5)

- [ ] **M4 — Kyverno** — resolve policy conflict, move to Enforce mode after audit
- [ ] **M5 — Vault + Venafi** — secrets management + PKI

### Phase 3 — Networking (Weeks 5–7)

- [ ] **M6 — Istio** — service mesh, mTLS, traffic management
- [ ] **M7 — Ingress** — AWS LBC, Nginx, External DNS, Cert Manager

### Phase 4 — Compute (Weeks 7–10)

- [ ] **M8 — Karpenter + KEDA** — dynamic node provisioning + event-driven scaling
- [ ] **M9 — GPU operator** — NVIDIA time slicing, DCGM metrics
- [ ] **M10 — Kafka** — Strimzi operator, real-time streaming

### Phase 5 — Observability + CI/CD (Weeks 10–12)

- [ ] **M11 — Monitoring** — Prometheus, Thanos, Grafana, Loki, OpenTelemetry
- [ ] **M12 — Supply chain** — Cosign, SBOM, Trivy, Grype
- [ ] **M13 — CI/CD** — GitHub Actions pipeline, ArgoCD GitOps
- [ ] **M14 — FinOps** — ResourceQuota, LimitRange, cost tagging

### Network Team Action Required

The TGW route table `tgw-rtb-06158adb9319962c6` needs a default route added to enable private subnet nodes:

```bash
aws ec2 create-transit-gateway-route \
  --transit-gateway-route-table-id tgw-rtb-06158adb9319962c6 \
  --destination-cidr-block 0.0.0.0/0 \
  --transit-gateway-attachment-id <HUB_VPC_ATTACHMENT_ID> \
  --region us-east-1
```

Once fixed, node group can be moved back to private subnets for better security posture.

---

## Key Learnings

### Terraform Workflow

**1. Always use plan files to avoid drift**

Never run `terraform apply` directly. Always save the plan to a file and apply that exact file. This guarantees what you reviewed is exactly what gets applied — no surprises if something changes between plan and apply.

```bash
# Step 1: Generate and save plan
terraform plan -out=m3.tfplan

# Step 2: Review the saved plan
terraform show m3.tfplan

# Step 3: Apply exactly what was planned
terraform apply m3.tfplan
```

If you run `terraform apply` without `-out`, Terraform re-plans at apply time. If any resource changed between your `plan` and `apply` (someone else applied, a resource was modified manually), the apply may do something different from what you reviewed.

---

**2. Use `terraform init -upgrade` when changing provider versions**

The `.terraform.lock.hcl` file pins exact provider versions. Simply changing the version constraint in `providers.tf` is not enough — you must re-run init with `-upgrade` to update the lock file.

```bash
# providers.tf — changed kubernetes from ~> 2.24 to ~> 3.1
# Just changing this file does NOT upgrade the provider

# Wrong — still uses old locked version
terraform init

# Correct — re-resolves versions and updates lock file
terraform init -upgrade

# Then verify new version is locked
cat .terraform.lock.hcl | grep -A3 "kubernetes"
```

Version constraint operators:

| Operator | Meaning | Example |
|----------|---------|---------|
| `= 3.1.0` | Exact version only | Only 3.1.0 |
| `~> 3.1` | Rightmost can increment | 3.1, 3.2, 3.9 but not 4.0 |
| `~> 3.1.0` | Patch only | 3.1.0, 3.1.9 but not 3.2.0 |
| `>= 3.1` | This version or newer | 3.1, 3.5, 4.0 all OK |

---

**3. Use `-migrate-state` when moving to remote backend**

When adding S3 backend to a project that previously used local state, use `-migrate-state` to copy existing state to S3. Without this, Terraform starts fresh and loses track of all existing resources.

```bash
# After adding backend.tf with S3 config:
terraform init -migrate-state

# Terraform prompts:
# "Do you want to copy existing state to the new backend? yes"

# Verify migration succeeded
aws s3 ls s3://eks-np01-tfstate-744958734165/eks-np01/
ls terraform.tfstate 2>/dev/null || echo "Confirmed: no local state"
```

| Init flag | When to use |
|-----------|-------------|
| `terraform init` | First time, or after adding new providers |
| `terraform init -upgrade` | After changing version constraints in providers.tf |
| `terraform init -migrate-state` | Moving state from local to remote (or remote to remote) |
| `terraform init -reconfigure` | Changing backend config without migrating state |

---

**4. Import before creating existing resources**

Always `terraform import` existing resources before trying to manage them. Otherwise Terraform tries to create duplicates and fails.

```bash
# Import existing cluster
terraform import aws_eks_cluster.eks_np01 eks-np01

# Import existing node group
terraform import aws_eks_node_group.bootstrap eks-np01:eks-np01-bootstrap

# After import — always run plan to find and fix drift
terraform plan
# Fix any differences until plan shows "No changes"
# THEN make new changes
```

---

**5. `bootstrap_self_managed_addons` must match existing cluster**

This computed attribute defaults to `true` in Terraform but existing clusters created via console/CLI default to `false`. Without explicitly setting it to `false`, Terraform forces a cluster destroy and recreate on every apply.

```hcl
resource "aws_eks_cluster" "eks_np01" {
  bootstrap_self_managed_addons = false  # must match existing cluster!
}
```

---

### Security & IAM

**6. IRSA is non-negotiable**

Any pod that needs AWS API access must have its own IAM role via IRSA. Using node IAM roles violates least-privilege principle — all pods on the node share the same permissions.

```
Node IAM role (bad):   ALL pods get ALL node permissions
IRSA (good):           Each pod gets ONLY its own permissions
```

---

**7. Taint awareness — DaemonSets vs Deployments**

DaemonSets tolerate all taints automatically. Deployments do not. Always check taints when system pods are stuck `Pending`.

```bash
# Check node taints
kubectl describe node <node> | grep Taints

# Check pod tolerations
kubectl get pod <pod> -o jsonpath='{.spec.tolerations}'
```

---

### State Management

**8. State is sacred**

Never delete state manually. Use proper commands:

```bash
terraform state list              # see all managed resources
terraform state show <resource>   # inspect a resource in state
terraform state rm <resource>     # stop managing (doesn't delete from AWS)
terraform import <resource> <id>  # start managing existing resource
terraform state mv <old> <new>    # rename resource in state
```

---

### Networking

**9. Hub-spoke TGW — verify route tables before placing nodes**

The existence of a TGW attachment does NOT guarantee internet routing. Always check which route table the VPC attachment is associated with and verify it has a `0.0.0.0/0` route.

```bash
# Check what route table your VPC attachment uses
aws ec2 get-transit-gateway-route-table-associations \
  --transit-gateway-route-table-id <rtb-id>

# Check routes in that table — look for 0.0.0.0/0
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id <rtb-id> \
  --filters "Name=type,Values=static,propagated"
```

---

### Operations

**10. Lifecycle hooks can block node group deletion**

AWS ASG lifecycle hooks from external systems (monitoring, CMDB, security tools) can hold node termination for up to the configured `HeartbeatTimeout` (often 30 minutes). Plan for this in CI/CD pipelines and destroy scripts.

```bash
# Check for lifecycle hooks on ASG
aws autoscaling describe-lifecycle-hooks \
  --auto-scaling-group-name <asg-name>

# Manually complete if external system isn't responding
aws autoscaling complete-lifecycle-action \
  --auto-scaling-group-name <asg-name> \
  --lifecycle-hook-name "Terminate-LC-Hook" \
  --lifecycle-action-result CONTINUE \
  --instance-id <instance-id>
```

---

**11. S3 native locking replaces DynamoDB (Terraform >= v1.10)**

```hcl
# Old way (deprecated)
backend "s3" {
  dynamodb_table = "my-lock-table"  # requires separate DynamoDB table
}

# New way (Terraform >= v1.10)
backend "s3" {
  use_lockfile = true  # uses S3 object lock, no extra resources needed
}
```

---

**12. `.gitignore` must exist BEFORE first commit**

The `.terraform/` folder contains provider binaries (500MB+) that must never be committed. Create `.gitignore` before `git add` or you'll have to purge git history.

```bash
# Always create .gitignore first
cat > .gitignore << 'EOF'
.terraform/
*.tfstate
*.tfstate.backup
*.tfplan
crash.log
*.tfvars
EOF

git add .gitignore
git commit -m "add .gitignore"
# THEN add your .tf files
```

If accidentally committed, remove from tracking:
```bash
git rm -r --cached .terraform/
git filter-repo --path .terraform/ --invert-paths --force
git push origin main --force
```
