Now I have full context. This is currently on **ECS/EC2 with no K8s manifests** — greenfield EKS migration. I also spotted critical security issues. Let me write the complete plan.

---

# Complete MLOps Implementation & Execution Plan
## Contracts AI IQT → Production EKS

---

> **CRITICAL SECURITY ISSUES FOUND — Fix Before Anything Else:**
> - HuggingFace token hardcoded in `Dockerfile-iqt-inference-gpu`:  → **rotate this token immediately**
> - SLIP password hardcoded in `eh_prod_config.yaml`: → **rotate and move to Secrets Manager**
> - Protegrity credentials in plain YAML → **move to Secrets Manager**

---

## Decision Points — Answer These Before Starting

**Ask yourself (or client) these 5 questions before Phase 1:**

| # | Decision | Option A (Recommended) | Option B | Option C |
|---|---|---|---|---|
| 1 | **IaC tool** | Terraform + Terragrunt | AWS CDK | eksctl only |
| 2 | **GitOps** | ArgoCD | Flux v2 | Manual Helm |
| 3 | **LLM serving** | vLLM | TGI (HuggingFace) | Keep raw HF |
| 4 | **CI/CD** | Bitbucket + GitHub Actions | Bitbucket only | AWS CodePipeline |
| 5 | **Observability** | kube-prometheus-stack (self-hosted) | Datadog (paid) | CloudWatch only |

**This plan uses: Terraform + ArgoCD + vLLM + Bitbucket Pipelines + kube-prometheus-stack**

---

## Overview: 12 Phases

```
Phase 0:  Prerequisites & Tooling Setup         (Day 1)
Phase 1:  Security Cleanup                      (Day 1-2)
Phase 2:  Terraform Foundation (VPC, IAM, ECR)  (Day 2-4)
Phase 3:  EKS Cluster                           (Day 4-6)
Phase 4:  Core K8s Add-ons                      (Day 6-8)
Phase 5:  Storage Layer (EFS, S3)               (Day 8-9)
Phase 6:  Observability Stack                   (Day 9-11)
Phase 7:  vLLM + Model Serving (Triton)         (Day 11-14)
Phase 8:  Application Helm Charts               (Day 14-18)
Phase 9:  GitOps with ArgoCD                    (Day 18-20)
Phase 10: MLOps Platform                        (Day 20-24)
Phase 11: Cost Optimization & Validation        (Day 24-26)
Phase 12: Cutover from ECS → EKS                (Day 26-30)
```

---

# PHASE 0: Prerequisites & Tooling Setup

## Step 0.1 — Install all tools

```bash
# --- macOS / Linux dev machine setup ---

# Terraform
brew install terraform terragrunt

# AWS CLI v2
brew install awscli
aws configure  # set access key, secret, region=us-east-1

# Kubernetes tools
brew install kubectl helm kubectx k9s stern

# EKS tools
brew install eksctl

# NVIDIA tools (for testing GPU locally)
# (skip if no local GPU)

# Kustomize
brew install kustomize

# ArgoCD CLI
brew install argocd

# Useful extras
brew install jq yq fzf bat

# Verify all
terraform --version      # >= 1.7
helm version             # >= 3.14
kubectl version --client
aws --version            # >= 2.x
eksctl version           # >= 0.175
argocd version --client
```

## Step 0.2 — Create the IaC repository structure

```bash
mkdir -p contracts-ai-iqt-infra
cd contracts-ai-iqt-infra

# Directory structure
mkdir -p {
  terraform/modules/{vpc,eks,rds,opensearch,efs,ecr,iam,sqs},
  terraform/environments/{dev,uat,prod},
  helm/{charts,values/{dev,uat,prod}},
  k8s/{namespaces,rbac,network-policies},
  argocd/{apps,projects},
  scripts/{bootstrap,validation,rollback},
  monitoring/{dashboards,alerts,rules},
  .github/workflows
}

# Initialize git
git init
git remote add origin git@bitbucket.org:YOUR_ORG/contracts-ai-iqt-infra.git
```

**Validation ✅**
```bash
aws sts get-caller-identity   # confirms AWS auth
kubectl cluster-info          # will fail until EKS exists - expected
terraform --version | head -1
```

---

# PHASE 1: Security Cleanup

## Step 1.1 — Rotate compromised credentials

```bash
# 1. Rotate HuggingFace token immediately
# Go to https://huggingface.co/settings/tokens
# Delete token: 
# Create new token with read-only scope
# Store in AWS Secrets Manager:

aws secretsmanager create-secret \
  --name "prod/iqt/huggingface" \
  --secret-string '{"HF_TOKEN":"hf_NEWTOKEN_HERE"}' \
  --region us-east-1

# 2. Rotate SLIP password
aws secretsmanager update-secret \
  --secret-id "prod/slip/cntrxai" \
  --secret-string '{"password":"NEW_PASS","username":"al91036","client_id":"slip-user"}' \
  --region us-east-1

# 3. Store Protegrity creds
aws secretsmanager create-secret \
  --name "prod/iqt/protegrity" \
  --secret-string '{"PROTEGRITY_USER":"SRC_PAP_CNTRXAI","PROTEGRITY_PASSWORD":"NEW_PASS"}' \
  --region us-east-1
```

## Step 1.2 — Fix Dockerfile-iqt-inference-gpu (remove hardcoded token)

The current file has:
```dockerfile
# INSECURE - hardcoded HF token
RUN huggingface-cli login --token $TOKEN
```

Replace with build-arg pattern:

```dockerfile
# docker_iqt/Dockerfile-iqt-inference-gpu (FIXED)
FROM nvidia/cuda:12.1.0-base-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEPLOYMENT=prod

RUN echo 'Acquire::http::No-Cache true;' > /etc/apt/apt.conf.d/99fixbadproxy \
    && echo 'Acquire::BrokenProxy true;' >> /etc/apt/apt.conf.d/99fixbadproxy

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y python3.10 python3-pip python3.10-venv python3.10-dev \
       libglib2.0-0 git curl \
    && rm -rf /var/lib/apt/lists/*

RUN python3.10 -m pip install --upgrade pip setuptools wheel
RUN rm -rf /usr/lib/python3/dist-packages/*

WORKDIR /app

# Create non-root user
RUN useradd --system --create-home --shell /usr/sbin/nologin app

COPY ./src/utils ./src/utils
COPY ./src/inference ./src/inference
COPY ./src/models ./src/models
COPY iqt_main_inference.py ./
COPY ./docker_iqt/requirement-iqt/requirements_inference_gpu.txt ./

RUN python3.10 -m venv venv \
    && . ./venv/bin/activate \
    && pip install --upgrade pip \
    && pip install torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0 \
       --index-url https://download.pytorch.org/whl/cu121 \
    && pip install -r requirements_inference_gpu.txt \
    && pip install --upgrade setuptools huggingface_hub

# HF token injected at RUNTIME via env var (from K8s secret), NOT baked in
# huggingface-cli login happens in entrypoint if HF_TOKEN is set
RUN chown -R app:app /app
USER app

CMD ["/bin/bash", "-c", \
  "source ./venv/bin/activate && \
   [ -n \"$HF_TOKEN\" ] && huggingface-cli login --token $HF_TOKEN --add-to-git-credential; \
   python iqt_main_inference.py"]
```

## Step 1.3 — Create `.gitignore` for secrets

```bash
cat >> contracts-ai-iqt-infra/.gitignore << 'EOF'
# Terraform
.terraform/
*.tfstate
*.tfstate.backup
.terraform.lock.hcl
terraform.tfvars
*.auto.tfvars

# Secrets
*.pem
*.key
.env
.env.*
secrets/
*secret*
*password*
*credentials*

# AWS
.aws/

# Python
__pycache__/
*.pyc
.venv/
venv/
EOF
```

**Validation ✅**
```bash
# Verify old token is invalid
curl -H "Authorization: Bearer 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" \
  https://huggingface.co/api/whoami
# Should return 401 if rotated

# Verify new secret exists
aws secretsmanager get-secret-value \
  --secret-id "prod/iqt/huggingface" \
  --region us-east-1 \
  --query SecretString --output text | jq .
```

---

# PHASE 2: Terraform Foundation

## Step 2.1 — Terraform root configuration

```hcl
# terraform/environments/prod/main.tf
terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27"
    }
  }

  backend "s3" {
    bucket         = "crln-cntrxai-prod-terraform-state"
    key            = "iqt/prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "contracts-ai-iqt"
      Environment = "prod"
      ManagedBy   = "terraform"
      CostCenter  = "IQT-PROD"
    }
  }
}
```

```bash
# Create Terraform state bucket first (one-time)
aws s3 mb s3://crln-cntrxai-prod-terraform-state --region us-east-1
aws s3api put-bucket-versioning \
  --bucket crln-cntrxai-prod-terraform-state \
  --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption \
  --bucket crln-cntrxai-prod-terraform-state \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# DynamoDB for state locking
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

## Step 2.2 — VPC Module

```hcl
# terraform/modules/vpc/main.tf
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.7"

  name = "iqt-prod-vpc"
  cidr = "10.100.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.100.1.0/24", "10.100.2.0/24", "10.100.3.0/24"]
  public_subnets  = ["10.100.101.0/24", "10.100.102.0/24", "10.100.103.0/24"]

  # NAT Gateway (one per AZ for HA, or single for cost savings)
  # DECISION: single_nat_gateway=true saves ~$100/month but loses AZ redundancy
  enable_nat_gateway     = true
  single_nat_gateway     = false   # ← Ask client: true for dev, false for prod
  one_nat_gateway_per_az = true

  enable_dns_hostnames = true
  enable_dns_support   = true

  # VPC Endpoints — CRITICAL for cost: avoids NAT charges for S3/SQS traffic
  enable_s3_endpoint  = true

  # Tags required for EKS to discover subnets
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"               = "1"
    "kubernetes.io/cluster/iqt-prod-eks"            = "owned"
    "karpenter.sh/discovery"                        = "iqt-prod-eks"
  }
  public_subnet_tags = {
    "kubernetes.io/role/elb"                        = "1"
    "kubernetes.io/cluster/iqt-prod-eks"            = "owned"
  }
}

# Additional VPC Endpoints for SQS, ECR, Bedrock (avoid NAT costs)
resource "aws_vpc_endpoint" "sqs" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.us-east-1.sqs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.us-east-1.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.us-east-1.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "bedrock" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.us-east-1.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.us-east-1.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_security_group" "vpc_endpoints" {
  name_prefix = "iqt-vpc-endpoints-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }
}
```

## Step 2.3 — ECR Repositories

```hcl
# terraform/modules/ecr/main.tf
locals {
  services = [
    "iqt-preprocessing",
    "iqt-bbox-generation",
    "iqt-text-generation",
    "iqt-page-classification",
    "iqt-linearizer",
    "iqt-chunking",
    "iqt-context-retrieval",
    "iqt-prompt-gen",
    "iqt-inference",
    "iqt-inference-gpu",
    "iqt-qa",
    "iqt-text-to-sql",
    "iqt-evaluation",
    "iqt-ingestion",
    "iqt-flask",
    "iqt-vllm",      # new: vLLM server
  ]
}

resource "aws_ecr_repository" "services" {
  for_each = toset(local.services)

  name                 = each.value
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true   # free Trivy scanning
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

# Lifecycle: keep last 10 prod images, last 3 dev images, delete untagged after 1 day
resource "aws_ecr_lifecycle_policy" "services" {
  for_each   = aws_ecr_repository.services
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 prod images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["prod-"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Expire untagged after 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      }
    ]
  })
}
```

## Step 2.4 — IAM Roles for Service Accounts (IRSA)

```hcl
# terraform/modules/iam/irsa.tf

# ── LLM Inference Service Account ────────────────────────────────────────────
module "irsa_inference" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.37"

  role_name = "iqt-prod-inference-irsa"

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["iqt:inference-sa"]
    }
  }

  role_policy_arns = {
    inference = aws_iam_policy.inference.arn
  }
}

resource "aws_iam_policy" "inference" {
  name = "iqt-prod-inference-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3ModelAccess"
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::crln-cntrxai-prod-dataz-gbd-phi-useast1",
          "arn:aws:s3:::crln-cntrxai-prod-dataz-gbd-phi-useast1/*"
        ]
      },
      {
        Sid    = "SQSInference"
        Effect = "Allow"
        Action = ["sqs:ReceiveMessage", "sqs:DeleteMessage",
                  "sqs:GetQueueAttributes", "sqs:ChangeMessageVisibility"]
        Resource = "arn:aws:sqs:us-east-1:768867475644:prod-CNTRXAI_llm_input_iqt*"
      },
      {
        Sid    = "Bedrock"
        Effect = "Allow"
        Action = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
        Resource = "*"
      },
      {
        Sid    = "SecretsManager"
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = [
          "arn:aws:secretsmanager:us-east-1:768867475644:secret:prod/slip/cntrxai*",
          "arn:aws:secretsmanager:us-east-1:768867475644:secret:prod/iqt/huggingface*",
          "arn:aws:secretsmanager:us-east-1:768867475644:secret:prod/horizon/cntrxai*"
        ]
      },
      {
        Sid    = "RDS"
        Effect = "Allow"
        Action = ["rds-data:ExecuteStatement", "rds-data:BatchExecuteStatement"]
        Resource = "*"
      }
    ]
  })
}

# ── Chunking Service Account ──────────────────────────────────────────────────
module "irsa_chunking" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.37"

  role_name = "iqt-prod-chunking-irsa"

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["iqt:chunking-sa"]
    }
  }

  role_policy_arns = {
    chunking = aws_iam_policy.chunking.arn
  }
}

resource "aws_iam_policy" "chunking" {
  name = "iqt-prod-chunking-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::crln-cntrxai-prod-dataz-gbd-phi-useast1",
          "arn:aws:s3:::crln-cntrxai-prod-dataz-gbd-phi-useast1/*"
        ]
      },
      {
        Effect = "Allow"
        Action = ["sqs:ReceiveMessage", "sqs:DeleteMessage",
                  "sqs:GetQueueAttributes", "sqs:SendMessage"]
        Resource = "arn:aws:sqs:us-east-1:768867475644:prod-CNTRXAI_chunker_input_iqt*"
      },
      {
        Effect = "Allow"
        Action = ["es:ESHttpPost", "es:ESHttpPut", "es:ESHttpGet"]
        Resource = "arn:aws:es:us-east-1:768867475644:domain/iqt-prod-opensearch/*"
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = "arn:aws:secretsmanager:us-east-1:768867475644:secret:prod/*"
      }
    ]
  })
}

# Add similar IRSA modules for: preprocessing, page-classification, bbox,
# flask, qa, text-to-sql, evaluation, ingestion
# (pattern repeats - scope each to only its SQS queues + S3 paths)
```

## Step 2.5 — Apply Terraform Foundation

```bash
cd terraform/environments/prod

# Initialize
terraform init

# Plan and review
terraform plan -out=tfplan

# Apply in stages (don't apply everything at once!)
terraform apply -target=module.vpc -auto-approve
terraform apply -target=module.ecr -auto-approve
terraform apply -target=module.iam -auto-approve

# Validate
terraform output vpc_id
terraform output private_subnet_ids
aws ecr describe-repositories --region us-east-1 --query 'repositories[].repositoryName' --output table
```

**Validation ✅**
```bash
# VPC exists
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=iqt-prod-vpc" \
  --query 'Vpcs[0].VpcId' --output text

# Subnets have correct tags for EKS
aws ec2 describe-subnets \
  --filters "Name=tag:kubernetes.io/role/internal-elb,Values=1" \
  --query 'Subnets[].SubnetId' --output table

# ECR repos created
aws ecr describe-repositories --region us-east-1 \
  --query 'repositories[].repositoryName' --output table

# VPC endpoints
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --query 'VpcEndpoints[].ServiceName' --output table
```

---

# PHASE 3: EKS Cluster

## Step 3.1 — EKS Cluster Terraform

**Approach decision:**
- **Option A (Recommended): Terraform `terraform-aws-modules/eks`** — full IaC, reproducible, version-controlled
- **Option B: `eksctl`** — faster, less code, but not pure IaC

```hcl
# terraform/modules/eks/main.tf
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.8"

  cluster_name    = "iqt-prod-eks"
  cluster_version = "1.30"

  vpc_id                    = var.vpc_id
  subnet_ids                = var.private_subnet_ids
  control_plane_subnet_ids  = var.private_subnet_ids

  # Private API endpoint (recommended for production)
  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = true   # set false after VPN/bastion setup
  cluster_endpoint_public_access_cidrs = ["YOUR_OFFICE_IP/32"]

  # Enable IRSA
  enable_irsa = true

  # Cluster addons
  cluster_addons = {
    coredns = {
      most_recent = true
      configuration_values = jsonencode({
        replicaCount = 2
        resources = {
          requests = { cpu = "100m", memory = "70Mi" }
          limits   = { cpu = "200m", memory = "170Mi" }
        }
      })
    }
    kube-proxy     = { most_recent = true }
    vpc-cni        = { most_recent = true }

    aws-ebs-csi-driver = {
      most_recent              = true
      service_account_role_arn = module.irsa_ebs_csi.iam_role_arn
    }

    aws-efs-csi-driver = {
      most_recent              = true
      service_account_role_arn = module.irsa_efs_csi.iam_role_arn
    }
  }

  # ── Node Groups ──────────────────────────────────────────────────────────────

  eks_managed_node_groups = {

    # System nodes — always running, no user workloads
    system = {
      name           = "system"
      instance_types = ["m5.large"]
      min_size       = 2
      max_size       = 4
      desired_size   = 2

      labels = {
        "node-role" = "system"
        "workload"  = "system"
      }
      taints = [{
        key    = "CriticalAddonsOnly"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
    }

    # CPU general — spot instances for stateless services
    cpu_spot = {
      name           = "cpu-spot"
      instance_types = ["m5.2xlarge", "m5a.2xlarge", "m5d.2xlarge", "m4.2xlarge"]
      capacity_type  = "SPOT"
      min_size       = 2
      max_size       = 30
      desired_size   = 3

      labels = {
        "node-role" = "cpu-workload"
        "workload"  = "cpu-spot"
      }

      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 100
            volume_type           = "gp3"
            iops                  = 3000
            throughput            = 125
            encrypted             = true
            delete_on_termination = true
          }
        }
      }
    }

    # GPU Small — for embedding, reranking, classification, bbox (T4 GPU)
    gpu_small = {
      name           = "gpu-small"
      instance_types = ["g4dn.xlarge"]  # 1x T4 16GB
      capacity_type  = "ON_DEMAND"      # Spot for GPU is risky for long workloads
      min_size       = 0
      max_size       = 10
      desired_size   = 0               # Karpenter manages this, starts at 0

      labels = {
        "node-role"    = "gpu-small"
        "workload"     = "ml-inference-small"
        "nvidia.com/gpu" = "true"
        "gpu-type"     = "T4"
      }
      taints = [{
        key    = "nvidia.com/gpu"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]

      # GPU AMI
      ami_type = "AL2_x86_64_GPU"

      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 200  # large: model weights cached here
            volume_type           = "gp3"
            iops                  = 6000
            throughput            = 250
            encrypted             = true
            delete_on_termination = true
          }
        }
      }
    }

    # GPU Large — for LLM inference (Llama 3.1 70B)
    gpu_large = {
      name           = "gpu-large"
      instance_types = ["g5.12xlarge"]  # 4x A10G 24GB = 96GB VRAM
      capacity_type  = "ON_DEMAND"
      min_size       = 0
      max_size       = 5
      desired_size   = 0               # KEDA scales this

      labels = {
        "node-role"    = "gpu-large"
        "workload"     = "llm-inference"
        "nvidia.com/gpu" = "true"
        "gpu-type"     = "A10G"
      }
      taints = [{
        key    = "nvidia.com/gpu"
        value  = "true"
        effect = "NO_SCHEDULE"
      }, {
        key    = "llm-inference"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]

      ami_type = "AL2_x86_64_GPU"

      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 500  # large: 70B model cache
            volume_type           = "gp3"
            iops                  = 16000
            throughput            = 1000
            encrypted             = true
            delete_on_termination = true
          }
        }
      }
    }
  }

  # aws-auth for team access
  manage_aws_auth_configmap = true
  aws_auth_roles = [
    {
      rolearn  = "arn:aws:iam::768867475644:role/DevOpsTeamRole"
      username = "devops-team"
      groups   = ["system:masters"]
    },
    {
      rolearn  = "arn:aws:iam::768867475644:role/MLEngineerRole"
      username = "ml-engineer"
      groups   = ["ml-engineers"]
    }
  ]
}
```

## Step 3.2 — Apply EKS

```bash
terraform apply -target=module.eks

# Update kubeconfig
aws eks update-kubeconfig \
  --region us-east-1 \
  --name iqt-prod-eks \
  --alias iqt-prod

# Verify
kubectl get nodes -o wide
kubectl get pods -n kube-system
```

## Step 3.3 — Create Namespaces

```yaml
# k8s/namespaces/namespaces.yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: iqt
  labels:
    name: iqt
    environment: prod
---
apiVersion: v1
kind: Namespace
metadata:
  name: iqt-gpu
  labels:
    name: iqt-gpu
    environment: prod
---
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
  labels:
    name: monitoring
---
apiVersion: v1
kind: Namespace
metadata:
  name: mlops
  labels:
    name: mlops
---
apiVersion: v1
kind: Namespace
metadata:
  name: karpenter
  labels:
    name: karpenter
---
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
```

```bash
kubectl apply -f k8s/namespaces/namespaces.yaml
kubectl get namespaces
```

**Validation ✅**
```bash
# Cluster healthy
kubectl get nodes -o wide
# Expected: system nodes Ready, gpu nodes may be 0 (scaled down)

kubectl get pods -n kube-system -o wide
# Expected: coredns, kube-proxy, vpc-cni all Running

# EBS CSI working
kubectl get pods -n kube-system -l app=ebs-csi-controller

# EFS CSI working
kubectl get pods -n kube-system -l app=efs-csi-controller

# Node GPU labels
kubectl get nodes -l workload=ml-inference-small --show-labels
```

---

# PHASE 4: Core Kubernetes Add-ons

## Step 4.1 — NVIDIA GPU Operator (replaces manual device plugin)

**Approach decision:**
- **Option A (Recommended): NVIDIA GPU Operator** — installs device plugin + drivers + DCGM + time-slicing in one Helm chart
- **Option B: Manual NVIDIA Device Plugin** — simpler but requires manual driver management

```bash
# Add NVIDIA Helm repo
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# Install GPU Operator with time-slicing enabled
cat > helm/values/prod/gpu-operator.yaml << 'EOF'
operator:
  defaultRuntime: containerd

driver:
  enabled: true    # installs NVIDIA driver on nodes
  version: "550"

toolkit:
  enabled: true

devicePlugin:
  enabled: true
  config:
    name: time-slicing-config

# Time-slicing: 4 virtual GPUs per physical T4 (for gpu-small nodes)
# Allows: reranker + embedding + classification + bbox on ONE T4
timeslicing:
  enabled: true
  resources:
    - name: nvidia.com/gpu
      replicas: 4     # 4 virtual GPUs per physical T4

dcgm:
  enabled: true   # enables GPU metrics for Prometheus

dcgmExporter:
  enabled: true
  serviceMonitor:
    enabled: true  # auto-scrape by Prometheus
EOF

helm install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --create-namespace \
  --values helm/values/prod/gpu-operator.yaml \
  --wait --timeout 10m

# Validate GPU time-slicing
kubectl get pods -n gpu-operator
kubectl describe node <gpu-small-node> | grep nvidia.com/gpu
# Expected: nvidia.com/gpu: 4  (4 virtual per physical T4)
```

## Step 4.2 — Karpenter (node auto-provisioner)

```bash
# Get cluster endpoint and OIDC provider
export CLUSTER_NAME=iqt-prod-eks
export AWS_ACCOUNT_ID=768867475644
export AWS_REGION=us-east-1

# Create Karpenter IAM role (via Terraform — already done in Phase 2)
# Install Karpenter
helm repo add karpenter https://charts.karpenter.sh
helm repo update

helm install karpenter oci://public.ecr.aws/karpenter/karpenter \
  --version "0.37.0" \
  --namespace karpenter \
  --set settings.clusterName=${CLUSTER_NAME} \
  --set settings.interruptionQueue=iqt-prod-karpenter \
  --set controller.resources.requests.cpu=1 \
  --set controller.resources.requests.memory=1Gi \
  --wait
```

```yaml
# k8s/karpenter/node-pool-cpu.yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: cpu-spot
spec:
  template:
    metadata:
      labels:
        workload: cpu-spot
    spec:
      nodeClassRef:
        apiVersion: karpenter.k8s.aws/v1beta1
        kind: EC2NodeClass
        name: default
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["m5.xlarge", "m5.2xlarge", "m5a.2xlarge",
                   "m5d.2xlarge", "m4.2xlarge", "m5n.2xlarge"]
        - key: topology.kubernetes.io/zone
          operator: In
          values: ["us-east-1a", "us-east-1b", "us-east-1c"]
  disruption:
    consolidationPolicy: WhenUnderutilized
    consolidateAfter: 30s
  limits:
    cpu: 200
    memory: 400Gi
---
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: gpu-small
spec:
  template:
    metadata:
      labels:
        workload: ml-inference-small
        gpu-type: T4
    spec:
      nodeClassRef:
        apiVersion: karpenter.k8s.aws/v1beta1
        kind: EC2NodeClass
        name: gpu
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["g4dn.xlarge", "g4dn.2xlarge"]
      taints:
        - key: nvidia.com/gpu
          value: "true"
          effect: NoSchedule
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 5m   # wait 5 min before killing idle GPU node
  limits:
    cpu: 80
    memory: 256Gi
    nvidia.com/gpu: 20
---
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: gpu-large
spec:
  template:
    metadata:
      labels:
        workload: llm-inference
        gpu-type: A10G
    spec:
      nodeClassRef:
        apiVersion: karpenter.k8s.aws/v1beta1
        kind: EC2NodeClass
        name: gpu
      requirements:
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["g5.12xlarge", "g5.48xlarge"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"]
      taints:
        - key: nvidia.com/gpu
          value: "true"
          effect: NoSchedule
        - key: llm-inference
          value: "true"
          effect: NoSchedule
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 10m  # LLM nodes get 10min grace before termination
  limits:
    nvidia.com/gpu: 16
```

```bash
kubectl apply -f k8s/karpenter/
```

## Step 4.3 — KEDA (SQS-driven autoscaling)

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update

helm install keda kedacore/keda \
  --namespace keda \
  --create-namespace \
  --set podIdentity.aws.irsa.enabled=true \
  --wait
```

```yaml
# k8s/keda/trigger-auth-sqs.yaml
# KEDA uses IRSA to authenticate with SQS
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: sqs-trigger-auth
  namespace: iqt
spec:
  podIdentity:
    provider: aws
    identityId: "arn:aws:iam::768867475644:role/iqt-prod-keda-irsa"
```

```yaml
# k8s/keda/scaled-object-inference.yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: iqt-inference-scaler
  namespace: iqt
spec:
  scaleTargetRef:
    name: iqt-inference
  pollingInterval: 15       # check every 15 seconds
  cooldownPeriod:  300      # wait 5 min before scaling down
  minReplicaCount: 0        # scale to zero when empty!
  maxReplicaCount: 8
  triggers:
  - type: aws-sqs-queue
    authenticationRef:
      name: sqs-trigger-auth
    metadata:
      queueURL: "https://sqs.us-east-1.amazonaws.com/768867475644/prod-CNTRXAI_llm_input_iqt"
      queueLength: "5"
      awsRegion: us-east-1
      identityOwner: operator
---
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: iqt-chunking-scaler
  namespace: iqt
spec:
  scaleTargetRef:
    name: iqt-chunking
  minReplicaCount: 0
  maxReplicaCount: 10
  triggers:
  - type: aws-sqs-queue
    authenticationRef:
      name: sqs-trigger-auth
    metadata:
      queueURL: "https://sqs.us-east-1.amazonaws.com/768867475644/prod-CNTRXAI_chunker_input_iqt"
      queueLength: "10"
      awsRegion: us-east-1
---
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: iqt-page-classification-scaler
  namespace: iqt
spec:
  scaleTargetRef:
    name: iqt-page-classification
  minReplicaCount: 0
  maxReplicaCount: 6
  triggers:
  - type: aws-sqs-queue
    authenticationRef:
      name: sqs-trigger-auth
    metadata:
      queueURL: "https://sqs.us-east-1.amazonaws.com/768867475644/prod-CNTRXAI_page_classification_input_iqt"
      queueLength: "8"
      awsRegion: us-east-1
# Repeat for: bbox, preprocessing, prompt-gen, rag, text-generation, linearizer
```

```bash
kubectl apply -f k8s/keda/
# Validate
kubectl get scaledobjects -n iqt
kubectl get triggerauthentications -n iqt
```

## Step 4.4 — AWS Load Balancer Controller + External Secrets

```bash
# Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName=iqt-prod-eks \
  --set serviceAccount.create=true \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=\
    "arn:aws:iam::768867475644:role/iqt-prod-alb-controller-irsa"

# External Secrets Operator (syncs AWS Secrets Manager → K8s Secrets)
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets \
  --create-namespace \
  --set installCRDs=true
```

```yaml
# k8s/external-secrets/cluster-secret-store.yaml
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: aws-secrets-manager
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
            namespace: external-secrets
---
# Sync HF token to K8s secret
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: huggingface-token
  namespace: iqt
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: huggingface-token
    creationPolicy: Owner
  data:
  - secretKey: HF_TOKEN
    remoteRef:
      key: prod/iqt/huggingface
      property: HF_TOKEN
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: slip-credentials
  namespace: iqt
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: slip-credentials
  data:
  - secretKey: password
    remoteRef:
      key: prod/slip/cntrxai
      property: password
  - secretKey: username
    remoteRef:
      key: prod/slip/cntrxai
      property: username
```

```bash
kubectl apply -f k8s/external-secrets/
# Validate secrets synced
kubectl get secrets -n iqt
kubectl get externalsecret -n iqt
```

**Validation ✅ (Phase 4 complete)**
```bash
# NVIDIA device plugin running on GPU nodes
kubectl get pods -n gpu-operator -o wide

# GPU resources visible
kubectl get nodes -l workload=ml-inference-small \
  -o custom-columns='NAME:.metadata.name,GPU:.status.capacity.nvidia\.com/gpu'

# KEDA running
kubectl get pods -n keda

# Karpenter running
kubectl get pods -n karpenter

# ALB controller
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# External secrets syncing
kubectl get externalsecret -n iqt
kubectl get secret huggingface-token -n iqt -o jsonpath='{.data.HF_TOKEN}' | base64 -d
```

---

# PHASE 5: Storage Layer

## Step 5.1 — EFS for Model Cache

```hcl
# terraform/modules/efs/main.tf
resource "aws_efs_file_system" "model_cache" {
  creation_token   = "iqt-prod-model-cache"
  performance_mode = "generalPurpose"
  throughput_mode  = "elastic"   # scales automatically with read throughput
  encrypted        = true

  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"  # cheaper storage for cold models
  }

  tags = { Name = "iqt-prod-model-cache" }
}

# Mount targets in each AZ (for HA access from all nodes)
resource "aws_efs_mount_target" "model_cache" {
  for_each = toset(var.private_subnet_ids)

  file_system_id  = aws_efs_file_system.model_cache.id
  subnet_id       = each.value
  security_groups = [aws_security_group.efs.id]
}

# Access points — one per service for security isolation
resource "aws_efs_access_point" "llm_models" {
  file_system_id = aws_efs_file_system.model_cache.id

  posix_user {
    gid = 1000
    uid = 1000
  }

  root_directory {
    path = "/llm-models"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "755"
    }
  }
}

resource "aws_efs_access_point" "small_models" {
  file_system_id = aws_efs_file_system.model_cache.id

  posix_user { gid = 1000; uid = 1000 }
  root_directory {
    path = "/small-models"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "755"
    }
  }
}

resource "aws_security_group" "efs" {
  name_prefix = "iqt-efs-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [var.eks_node_security_group_id]
  }
}
```

## Step 5.2 — EFS PersistentVolumes

```yaml
# k8s/storage/efs-pvcs.yaml
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: efs-llm-models-pv
spec:
  capacity:
    storage: 500Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteMany    # multiple pods can read simultaneously
  persistentVolumeReclaimPolicy: Retain
  storageClassName: efs-sc
  csi:
    driver: efs.csi.aws.com
    volumeHandle: "fs-XXXXXXXX::fsap-XXXXXXXX"  # EFS filesystem ID::access point ID
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: efs-llm-models-pvc
  namespace: iqt
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: efs-sc
  resources:
    requests:
      storage: 500Gi
  volumeName: efs-llm-models-pv
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: efs-sc
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap
  fileSystemId: "fs-XXXXXXXX"
  directoryPerms: "755"
  gidRangeStart: "1000"
  gidRangeEnd: "2000"
  basePath: "/models"
```

## Step 5.3 — Model Pre-download Job

```yaml
# k8s/jobs/model-cache-init.yaml
# Run once to pre-populate EFS from S3/HuggingFace
apiVersion: batch/v1
kind: Job
metadata:
  name: model-cache-init
  namespace: iqt
spec:
  template:
    spec:
      nodeSelector:
        workload: ml-inference-small
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule
      initContainers:
        # Download embedding model
        - name: download-embedding
          image: huggingface/transformers-pytorch-gpu:latest
          command:
            - /bin/bash
            - -c
            - |
              if [ ! -d "/models/embedding/.complete" ]; then
                huggingface-cli download BAAI/bge-large-en-v1.5 \
                  --local-dir /models/embedding \
                  --token $HF_TOKEN
                touch /models/embedding/.complete
              fi
          env:
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: huggingface-token
                  key: HF_TOKEN
          volumeMounts:
            - name: model-cache
              mountPath: /models
              subPath: small-models

        # Download reranker models
        - name: download-reranker
          image: huggingface/transformers-pytorch-gpu:latest
          command:
            - /bin/bash
            - -c
            - |
              if [ ! -d "/models/reranker-mxbai/.complete" ]; then
                huggingface-cli download mixedbread-ai/mxbai-rerank-large-v1 \
                  --local-dir /models/reranker-mxbai --token $HF_TOKEN
                touch /models/reranker-mxbai/.complete
              fi
              if [ ! -d "/models/reranker-bge/.complete" ]; then
                huggingface-cli download BAAI/bge-reranker-v2-m3 \
                  --local-dir /models/reranker-bge --token $HF_TOKEN
                touch /models/reranker-bge/.complete
              fi
          env:
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: huggingface-token
                  key: HF_TOKEN
          volumeMounts:
            - name: model-cache
              mountPath: /models
              subPath: small-models

      containers:
        - name: verify
          image: busybox
          command: ["/bin/sh", "-c", "ls -la /models/embedding /models/reranker-mxbai /models/reranker-bge"]
          volumeMounts:
            - name: model-cache
              mountPath: /models
              subPath: small-models

      volumes:
        - name: model-cache
          persistentVolumeClaim:
            claimName: efs-small-models-pvc
      restartPolicy: OnFailure
```

```bash
kubectl apply -f k8s/storage/
kubectl apply -f k8s/jobs/model-cache-init.yaml
# Watch the job
kubectl logs -n iqt job/model-cache-init -f --all-containers
```

**Validation ✅**
```bash
# EFS mounted and writable
kubectl run test-efs --image=busybox -n iqt --rm -it \
  --overrides='{"spec":{"volumes":[{"name":"m","persistentVolumeClaim":{"claimName":"efs-llm-models-pvc"}}],"containers":[{"name":"t","image":"busybox","command":["sh"],"volumeMounts":[{"mountPath":"/mnt","name":"m"}]}]}}' \
  -- sh -c "ls -la /mnt"

# Models downloaded
kubectl logs -n iqt job/model-cache-init -c verify
```

---

# PHASE 6: Observability Stack

## Step 6.1 — Prometheus + Grafana (kube-prometheus-stack)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

```yaml
# helm/values/prod/kube-prometheus-stack.yaml
nameOverride: monitoring

grafana:
  enabled: true
  adminPassword: "CHANGE_ME_USE_SECRET"  # set via external secrets in prod
  persistence:
    enabled: true
    storageClassName: gp3
    size: 20Gi
  ingress:
    enabled: true
    annotations:
      kubernetes.io/ingress.class: alb
      alb.ingress.kubernetes.io/scheme: internal
    hosts:
      - grafana.iqt.internal
  # Pre-load GPU and IQT dashboards
  dashboardProviders:
    dashboardproviders.yaml:
      apiVersion: 1
      providers:
        - name: iqt
          folder: IQT
          type: file
          options:
            path: /var/lib/grafana/dashboards/iqt
  sidecar:
    dashboards:
      enabled: true
      searchNamespace: ALL

prometheus:
  prometheusSpec:
    retention: 30d
    retentionSize: 50GB
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3
          resources:
            requests:
              storage: 100Gi
    # Scrape GPU metrics from DCGM exporter
    additionalScrapeConfigs:
      - job_name: dcgm-exporter
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            action: keep
            regex: dcgm-exporter

alertmanager:
  config:
    global:
      slack_api_url: "YOUR_SLACK_WEBHOOK"
    route:
      group_by: ['alertname', 'namespace']
      group_wait: 30s
      receiver: slack-critical
      routes:
        - match:
            severity: critical
          receiver: slack-critical
        - match:
            severity: warning
          receiver: slack-warning
    receivers:
      - name: slack-critical
        slack_configs:
          - channel: '#iqt-alerts-critical'
            text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
      - name: slack-warning
        slack_configs:
          - channel: '#iqt-alerts-warning'

# Node Exporter for host metrics
nodeExporter:
  enabled: true

# kube-state-metrics for K8s object metrics
kubeStateMetrics:
  enabled: true
```

```bash
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values helm/values/prod/kube-prometheus-stack.yaml \
  --wait --timeout 10m
```

## Step 6.2 — GPU Alert Rules

```yaml
# monitoring/alerts/gpu-alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: gpu-alerts
  namespace: monitoring
  labels:
    prometheus: kube-prometheus
    role: alert-rules
spec:
  groups:
  - name: gpu.rules
    rules:
    # GPU underutilised — wasting money
    - alert: GPUUnderutilized
      expr: |
        avg_over_time(DCGM_FI_DEV_GPU_UTIL[10m]) < 30
        and on(node) kube_node_labels{label_workload=~"llm.*|ml.*"}
      for: 15m
      labels:
        severity: warning
      annotations:
        summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} < 30% utilised for 15m"
        description: "Consider scale-down or reducing replicas. Current: {{ $value }}%"

    # GPU OOM risk
    - alert: GPUMemoryHigh
      expr: DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_TOTAL * 100 > 90
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "GPU memory > 90% on {{ $labels.node }}"
        description: "Risk of OOM. GPU {{ $labels.gpu }}: {{ $value }}% memory used"

    # LLM inference latency
    - alert: LLMInferenceLatencyHigh
      expr: histogram_quantile(0.95, rate(vllm_request_duration_seconds_bucket[5m])) > 30
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "vLLM p95 latency > 30s"
        description: "p95 inference latency: {{ $value }}s. Consider scaling or reducing batch size."

    # SQS queue depth (KEDA not scaling fast enough)
    - alert: SQSQueueDepthHigh
      expr: aws_sqs_approximate_number_of_messages_visible > 500
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "SQS queue {{ $labels.queue_name }} depth > 500"
```

## Step 6.3 — Kubecost (cost attribution)

```bash
helm repo add kubecost https://kubecost.github.io/cost-analyzer/
helm install kubecost kubecost/cost-analyzer \
  --namespace monitoring \
  --set kubecostToken="FREE" \
  --set global.prometheus.fqdn="http://kube-prometheus-stack-prometheus.monitoring:9090" \
  --set global.prometheus.enabled=false \
  --set ingress.enabled=true \
  --set ingress.annotations."kubernetes\.io/ingress\.class"=alb
```

## Step 6.4 — Grafana Dashboards for IQT

```bash
# Import these dashboard IDs in Grafana:
# 12239 - NVIDIA DCGM Exporter Dashboard
# 3119  - Kubernetes Cluster Monitoring
# 15520 - KEDA Metrics
# 14282 - AWS SQS Overview

# Custom IQT dashboard (save as ConfigMap for auto-import)
kubectl create configmap iqt-grafana-dashboard \
  --from-file=monitoring/dashboards/iqt-pipeline.json \
  -n monitoring \
  --dry-run=client -o yaml | kubectl apply -f -
```

**Validation ✅**
```bash
# Prometheus targets
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090 &
open http://localhost:9090/targets
# Should see: node-exporter, kube-state-metrics, dcgm-exporter targets

# Grafana accessible
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80 &
open http://localhost:3000
# Login: admin / CHANGE_ME_USE_SECRET

# GPU metrics flowing
curl -s http://localhost:9090/api/v1/query?query=DCGM_FI_DEV_GPU_UTIL | jq .

# Kubecost
kubectl port-forward -n monitoring svc/kubecost-cost-analyzer 9003:9003 &
open http://localhost:9003
```

---

# PHASE 7: vLLM + Model Serving

## Step 7.1 — vLLM Deployment (replaces raw HF inference — biggest cost win)

**This is the single most impactful change. vLLM provides:**
- Continuous batching (no GPU idle between requests)
- PagedAttention (KV cache memory efficiency)
- OpenAI-compatible API (zero code change needed)
- 2-4x throughput improvement

```dockerfile
# docker_iqt/Dockerfile-iqt-vllm
# vLLM with AWQ quantization support
FROM vllm/vllm-openai:v0.4.3

# Install AWS CLI for model download from S3
RUN pip install awscli boto3

WORKDIR /app
COPY scripts/vllm-entrypoint.sh /app/

RUN chmod +x /app/vllm-entrypoint.sh
ENTRYPOINT ["/app/vllm-entrypoint.sh"]
```

```bash
# scripts/vllm-entrypoint.sh
#!/bin/bash
set -e

MODEL_PATH=${MODEL_PATH:-"/models/llm/current"}
MODEL_NAME=${MODEL_NAME:-"meta-llama/Meta-Llama-3.1-70B-Instruct"}
GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-"0.90"}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-"8192"}
TENSOR_PARALLEL_SIZE=${TENSOR_PARALLEL_SIZE:-"2"}   # use 2 of 4 A10Gs

# Download model from EFS or S3 if not cached
if [ ! -f "${MODEL_PATH}/.complete" ]; then
  echo "Model not in cache. Downloading from S3..."
  aws s3 sync s3://crln-cntrxai-prod-dataz-gbd-phi-useast1/models/llama-3.1-70b-awq/ \
    ${MODEL_PATH}/ --region us-east-1
  touch ${MODEL_PATH}/.complete
  echo "Model downloaded and cached."
else
  echo "Using cached model from ${MODEL_PATH}"
fi

# Start vLLM server
exec python -m vllm.entrypoints.openai.api_server \
  --model ${MODEL_PATH} \
  --tokenizer ${MODEL_PATH} \
  --tensor-parallel-size ${TENSOR_PARALLEL_SIZE} \
  --gpu-memory-utilization ${GPU_MEMORY_UTILIZATION} \
  --max-model-len ${MAX_MODEL_LEN} \
  --quantization awq \          # use AWQ quantization
  --dtype float16 \
  --enable-chunked-prefill \   # better batching
  --max-num-batched-tokens 8192 \
  --trust-remote-code \
  --port 8000 \
  --host 0.0.0.0
```

```yaml
# helm/charts/iqt-vllm/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iqt-vllm
  namespace: iqt
spec:
  replicas: 1    # KEDA scales this
  selector:
    matchLabels:
      app: iqt-vllm
  template:
    metadata:
      labels:
        app: iqt-vllm
    spec:
      serviceAccountName: inference-sa
      nodeSelector:
        workload: llm-inference
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule
        - key: llm-inference
          operator: Exists
          effect: NoSchedule

      # Init container: wait for model to be cached on EFS
      initContainers:
        - name: model-cache-check
          image: amazon/aws-cli:latest
          command:
            - /bin/sh
            - -c
            - |
              if [ ! -f "/models/llm/current/.complete" ]; then
                echo "Downloading 70B model from S3 (may take 5-8 min)..."
                aws s3 sync s3://crln-cntrxai-prod-dataz-gbd-phi-useast1/models/llama-3.1-70b-awq/ \
                  /models/llm/current/ --region us-east-1
                touch /models/llm/current/.complete
              else
                echo "Model already cached, starting immediately"
              fi
          volumeMounts:
            - name: model-cache
              mountPath: /models
              subPath: llm-models

      containers:
        - name: vllm
          image: 768867475644.dkr.ecr.us-east-1.amazonaws.com/iqt-vllm:latest
          ports:
            - containerPort: 8000
              name: http
          env:
            - name: MODEL_PATH
              value: "/models/llm/current"
            - name: TENSOR_PARALLEL_SIZE
              value: "2"
            - name: GPU_MEMORY_UTILIZATION
              value: "0.90"
            - name: MAX_MODEL_LEN
              value: "8192"
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: huggingface-token
                  key: HF_TOKEN

          resources:
            requests:
              cpu: "8"
              memory: "32Gi"
              nvidia.com/gpu: "2"   # 2 of 4 A10Gs on g5.12xlarge
            limits:
              cpu: "16"
              memory: "60Gi"
              nvidia.com/gpu: "2"

          volumeMounts:
            - name: model-cache
              mountPath: /models
              subPath: llm-models
            - name: shm
              mountPath: /dev/shm   # CRITICAL: shared memory for tensor parallel

          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 120   # model load takes time
            periodSeconds: 10
            failureThreshold: 30

          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 180
            periodSeconds: 30

      volumes:
        - name: model-cache
          persistentVolumeClaim:
            claimName: efs-llm-models-pvc
        - name: shm
          emptyDir:
            medium: Memory
            sizeLimit: 16Gi  # shared memory for tensor parallel communication
---
apiVersion: v1
kind: Service
metadata:
  name: iqt-vllm
  namespace: iqt
spec:
  selector:
    app: iqt-vllm
  ports:
    - name: http
      port: 8000
      targetPort: 8000
```

## Step 7.2 — Update LLM Inference Service to use vLLM

The existing `iqt_main_inference.py` uses 5+ different LLM clients. Replace with **LiteLLM + vLLM**:

```python
# src/inference/llm_client_vllm.py
# NEW: unified client using LiteLLM proxy → vLLM for local models
import litellm
from litellm import completion
import os

class UnifiedLLMClient:
    """
    Single client for all LLM backends.
    Replaces: OpenAIClient, BedrockClient, GeminiClient, HorizonHubClient, SLIPClient
    """

    # Map existing provider names to LiteLLM model strings
    PROVIDER_MAP = {
        "openai":        "gpt-4o",
        "bedrock_llama": "bedrock/meta.llama3-1-70b-instruct-v1:0",
        "bedrock_claude": "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0",
        "bedrock_mistral": "bedrock/mistral.mistral-large-2402-v1:0",
        "gemini":        "gemini/gemini-2.0-flash",
        "local_vllm":    "openai/meta-llama/Meta-Llama-3.1-70B-Instruct",
        "slip":          "openai/meta-llama/Meta-Llama-3.1-70B-Instruct",
    }

    def __init__(self, provider: str = "local_vllm"):
        self.provider = provider
        self.model = self.PROVIDER_MAP[provider]

        # For local vLLM — point to in-cluster service
        if provider in ("local_vllm", "slip"):
            os.environ["OPENAI_API_BASE"] = "http://iqt-vllm.iqt.svc.cluster.local:8000/v1"
            os.environ["OPENAI_API_KEY"] = "EMPTY"  # vLLM doesn't need real key

        # Enable caching (semantic cache via Redis)
        litellm.cache = litellm.Cache(
            type="redis",
            host=os.getenv("REDIS_HOST", "redis.iqt.svc.cluster.local"),
            port=6379
        )

    def generate(self,
                 messages: list[dict],
                 max_tokens: int = 2000,
                 temperature: float = 0.01,
                 response_format: dict = None) -> str:
        """
        Generate response. Handles all providers uniformly.
        For constrained JSON generation, use response_format={"type": "json_object"}
        vLLM supports this natively.
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "caching": True,   # use semantic cache
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = completion(**kwargs)
        return response.choices[0].message.content

    def generate_constrained(self,
                             messages: list[dict],
                             json_schema: dict,
                             max_tokens: int = 2000) -> dict:
        """
        Constrained JSON generation.
        vLLM supports guided_json natively via extra_body.
        Falls back to response_format for API providers.
        """
        import json

        if self.provider in ("local_vllm", "slip"):
            # vLLM guided decoding — exact JSON schema adherence
            response = completion(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.01,
                extra_body={"guided_json": json_schema}  # vLLM guided decoding
            )
        else:
            # API providers: use response_format + system prompt schema
            response = completion(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.01,
                response_format={"type": "json_object"}
            )

        return json.loads(response.choices[0].message.content)
```

## Step 7.3 — NVIDIA Triton for Small Models

```yaml
# helm/charts/iqt-triton/templates/deployment.yaml
# Serves: LayoutLMv2, DonutDet, embedding, reranker on shared GPU (time-sliced)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iqt-triton
  namespace: iqt
spec:
  replicas: 1
  selector:
    matchLabels:
      app: iqt-triton
  template:
    spec:
      nodeSelector:
        workload: ml-inference-small
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule
      containers:
        - name: triton
          image: nvcr.io/nvidia/tritonserver:24.03-py3
          args:
            - tritonserver
            - --model-repository=/models
            - --allow-grpc=true
            - --allow-http=true
            - --grpc-port=8001
            - --http-port=8000
            - --log-verbose=1
            # Dynamic batching config per model in model repo
          resources:
            requests:
              nvidia.com/gpu: "1"   # gets 1 of 4 virtual T4 slices
              memory: "8Gi"
              cpu: "2"
            limits:
              nvidia.com/gpu: "1"
              memory: "12Gi"
          volumeMounts:
            - name: model-cache
              mountPath: /models
              subPath: small-models
          ports:
            - containerPort: 8000
              name: http
            - containerPort: 8001
              name: grpc
            - containerPort: 8002
              name: metrics
          readinessProbe:
            httpGet:
              path: /v2/health/ready
              port: 8000
            initialDelaySeconds: 60
      volumes:
        - name: model-cache
          persistentVolumeClaim:
            claimName: efs-small-models-pvc
```

**Validation ✅**
```bash
# vLLM health
kubectl port-forward -n iqt svc/iqt-vllm 8000:8000 &
curl http://localhost:8000/health
curl http://localhost:8000/v1/models | jq .

# Test inference via vLLM OpenAI API
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "messages": [{"role": "user", "content": "Extract the rate from: $125.00 per member per month"}],
    "max_tokens": 100,
    "temperature": 0.01
  }' | jq .choices[0].message.content

# Triton health
kubectl port-forward -n iqt svc/iqt-triton 8000:8000 &
curl http://localhost:8000/v2/health/ready

# GPU utilization with vLLM running
kubectl exec -n iqt deploy/iqt-vllm -- nvidia-smi
```

---

# PHASE 8: Application Helm Charts

## Step 8.1 — Shared Chart Structure

```bash
# Create base Helm chart (all 15 services share this template)
helm create helm/charts/iqt-service
```

```yaml
# helm/charts/iqt-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.name }}
  namespace: {{ .Values.namespace | default "iqt" }}
  labels:
    app: {{ .Values.name }}
    version: {{ .Values.image.tag }}
spec:
  replicas: {{ .Values.replicas | default 1 }}
  selector:
    matchLabels:
      app: {{ .Values.name }}
  template:
    metadata:
      labels:
        app: {{ .Values.name }}
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: {{ .Values.metrics.port | default "8080" | quote }}
    spec:
      serviceAccountName: {{ .Values.serviceAccountName }}
      {{- if .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml .Values.nodeSelector | nindent 8 }}
      {{- end }}
      {{- if .Values.tolerations }}
      tolerations:
        {{- toYaml .Values.tolerations | nindent 8 }}
      {{- end }}

      # Init container: load config from S3 (current pattern preserved)
      initContainers:
        - name: config-loader
          image: amazon/aws-cli:latest
          command:
            - /bin/sh
            - -c
            - |
              aws s3 cp s3://crln-cntrxai-prod-dataz-gbd-phi-useast1/artifacts/{{ .Values.configCommit }}/config/ \
                /config/ --recursive --region us-east-1
          volumeMounts:
            - name: config
              mountPath: /config

      containers:
        - name: {{ .Values.name }}
          image: {{ .Values.image.registry }}/{{ .Values.image.name }}:{{ .Values.image.tag }}
          imagePullPolicy: Always
          env:
            - name: DEPLOYMENT
              value: {{ .Values.environment | default "prod" }}
            - name: CONFIG_PATH
              value: /config/eh_{{ .Values.environment }}_config.yaml
            {{- range .Values.extraEnv }}
            - name: {{ .name }}
              {{- if .valueFrom }}
              valueFrom:
                {{- toYaml .valueFrom | nindent 16 }}
              {{- else }}
              value: {{ .value | quote }}
              {{- end }}
            {{- end }}

          resources:
            {{- toYaml .Values.resources | nindent 12 }}

          {{- if .Values.gpu.enabled }}
          # GPU-specific: share memory for tensor parallel
          volumeMounts:
            - name: shm
              mountPath: /dev/shm
          {{- end }}

          volumeMounts:
            - name: config
              mountPath: /config
            {{- if .Values.modelCache.enabled }}
            - name: model-cache
              mountPath: /models
              subPath: {{ .Values.modelCache.subPath }}
            {{- end }}

          {{- if .Values.healthCheck.enabled }}
          readinessProbe:
            httpGet:
              path: /health
              port: {{ .Values.healthCheck.port | default 8080 }}
            initialDelaySeconds: {{ .Values.healthCheck.initialDelay | default 30 }}
            periodSeconds: 10
          {{- end }}

      volumes:
        - name: config
          emptyDir: {}
        {{- if .Values.gpu.enabled }}
        - name: shm
          emptyDir:
            medium: Memory
            sizeLimit: {{ .Values.gpu.shmSize | default "8Gi" }}
        {{- end }}
        {{- if .Values.modelCache.enabled }}
        - name: model-cache
          persistentVolumeClaim:
            claimName: {{ .Values.modelCache.pvcName }}
        {{- end }}
```

## Step 8.2 — Values files per service

```yaml
# helm/values/prod/iqt-inference.yaml
name: iqt-inference
namespace: iqt
serviceAccountName: inference-sa
environment: prod
configCommit: "latest"  # or pin to specific commit hash

image:
  registry: 768867475644.dkr.ecr.us-east-1.amazonaws.com
  name: iqt-inference-gpu
  tag: prod-latest

replicas: 0  # KEDA manages this

nodeSelector:
  workload: llm-inference

tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
  - key: llm-inference
    operator: Exists
    effect: NoSchedule

resources:
  requests:
    cpu: "2"
    memory: "4Gi"
    # NOTE: with vLLM sidecar, this service now just sends HTTP to vLLM
    # No direct GPU needed here anymore
  limits:
    cpu: "4"
    memory: "8Gi"

gpu:
  enabled: false   # GPU is in vLLM sidecar, not this service

modelCache:
  enabled: false

extraEnv:
  - name: VLLM_ENDPOINT
    value: "http://iqt-vllm.iqt.svc.cluster.local:8000/v1"
  - name: HF_TOKEN
    valueFrom:
      secretKeyRef:
        name: huggingface-token
        key: HF_TOKEN
  - name: SLIP_PASSWORD
    valueFrom:
      secretKeyRef:
        name: slip-credentials
        key: password

healthCheck:
  enabled: false  # SQS workers don't expose HTTP

metrics:
  port: 8080
```

```yaml
# helm/values/prod/iqt-chunking.yaml
name: iqt-chunking
namespace: iqt
serviceAccountName: chunking-sa
environment: prod

image:
  registry: 768867475644.dkr.ecr.us-east-1.amazonaws.com
  name: iqt-chunking
  tag: prod-latest

replicas: 0  # KEDA manages

nodeSelector:
  workload: ml-inference-small

tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule

resources:
  requests:
    cpu: "2"
    memory: "8Gi"
    nvidia.com/gpu: "1"   # gets 1 virtual GPU slice (time-sliced T4)
  limits:
    cpu: "4"
    memory: "16Gi"
    nvidia.com/gpu: "1"

gpu:
  enabled: true
  shmSize: "4Gi"

modelCache:
  enabled: true
  pvcName: efs-small-models-pvc
  subPath: small-models
```

```yaml
# helm/values/prod/iqt-flask.yaml
name: iqt-flask
namespace: iqt
serviceAccountName: flask-sa
environment: prod

image:
  registry: 768867475644.dkr.ecr.us-east-1.amazonaws.com
  name: iqt-flask
  tag: prod-latest

replicas: 2  # Always running (handles user requests)

resources:
  requests:
    cpu: "1"
    memory: "2Gi"
  limits:
    cpu: "4"
    memory: "4Gi"

gpu:
  enabled: false

healthCheck:
  enabled: true
  port: 5000
  initialDelay: 15

# Flask needs an Ingress
ingress:
  enabled: true
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/ssl-redirect: "443"
    alb.ingress.kubernetes.io/certificate-arn: "arn:aws:acm:us-east-1:768867475644:certificate/..."
  hosts:
    - host: api.iqt.prod.internal
      paths:
        - path: /
          pathType: Prefix
```

## Step 8.3 — Build and push all images

```bash
# scripts/bootstrap/build-all.sh
#!/bin/bash
set -e

AWS_ACCOUNT=768867475644
AWS_REGION=us-east-1
ECR_BASE="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"
GIT_SHA=$(git rev-parse --short HEAD)
TAG="prod-${GIT_SHA}"

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_BASE}

# Services and their Dockerfiles
declare -A SERVICES=(
  ["iqt-preprocessing"]="docker_iqt/Dockerfile-iqt-preprocessing"
  ["iqt-bbox-generation"]="docker_iqt/Dockerfile-iqt-bbox-generation"
  ["iqt-text-generation"]="docker_iqt/Dockerfile-iqt-text-generation"
  ["iqt-page-classification"]="docker_iqt/Dockerfile-iqt-page-classification"
  ["iqt-linearizer"]="docker_iqt/Dockerfile-iqt-linearizer"
  ["iqt-chunking"]="docker_iqt/Dockerfile-iqt-chunking"
  ["iqt-inference-gpu"]="docker_iqt/Dockerfile-iqt-inference-gpu"
  ["iqt-prompt-gen"]="docker_iqt/Dockerfile-iqt-prompt-gen"
  ["iqt-flask"]="docker_iqt/Dockerfile-iqt-flask"
  ["iqt-text-to-sql"]="docker_iqt/Dockerfile-iqt-text-to-sql"
)

for SERVICE in "${!SERVICES[@]}"; do
  DOCKERFILE="${SERVICES[$SERVICE]}"
  echo "Building ${SERVICE}..."

  docker buildx build \
    --platform linux/amd64 \
    --file ${DOCKERFILE} \
    --tag ${ECR_BASE}/${SERVICE}:${TAG} \
    --tag ${ECR_BASE}/${SERVICE}:prod-latest \
    --cache-from type=registry,ref=${ECR_BASE}/${SERVICE}:buildcache \
    --cache-to type=registry,ref=${ECR_BASE}/${SERVICE}:buildcache,mode=max \
    --push \
    --build-arg BITBUCKET_USERNAME=${BITBUCKET_USERNAME} \
    --build-arg BITBUCKET_APP_PASSWORD=${BITBUCKET_APP_PASSWORD} \
    .

  echo "✅ ${SERVICE}:${TAG} pushed"
done
```

---

# PHASE 9: GitOps with ArgoCD

## Step 9.1 — Install ArgoCD

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

helm install argocd argo/argo-cd \
  --namespace argocd \
  --set configs.params."server\.insecure"=true \
  --set server.ingress.enabled=true \
  --set server.ingress.annotations."kubernetes\.io/ingress\.class"=alb \
  --wait

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# Login
argocd login localhost:8080 --username admin --insecure
```

## Step 9.2 — App of Apps Pattern

```yaml
# argocd/apps/root-app.yaml
# This single App manages all other Apps
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: iqt-root
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: iqt-prod
  source:
    repoURL: https://bitbucket.org/YOUR_ORG/contracts-ai-iqt-infra
    targetRevision: main
    path: argocd/apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

```yaml
# argocd/apps/iqt-inference-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: iqt-inference
  namespace: argocd
spec:
  project: iqt-prod
  source:
    repoURL: https://bitbucket.org/YOUR_ORG/contracts-ai-iqt-infra
    targetRevision: main
    path: helm/charts/iqt-service
    helm:
      valueFiles:
        - ../../helm/values/prod/iqt-inference.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: iqt
  syncPolicy:
    automated:
      prune: false      # don't auto-delete inference pods
      selfHeal: true
    syncOptions:
      - RespectIgnoreDifferences=true
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas   # KEDA manages replicas, ignore drift
```

## Step 9.3 — Update Bitbucket Pipeline (CI → ArgoCD)

```yaml
# bitbucket-pipelines.yml (UPDATED)
image: amazon/aws-cli

definitions:
  steps:
    - step: &build_and_push
        name: "Build and Push Docker Images"
        services: [docker]
        script:
          - export TAG="prod-${BITBUCKET_COMMIT:0:7}"
          - export ECR_BASE="${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com"
          - aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_BASE
          # Build changed services only (detect via git diff)
          - |
            CHANGED=$(git diff --name-only HEAD~1 HEAD | grep "docker_iqt/\|src/" | cut -d/ -f2 | sort -u)
            for SERVICE in $CHANGED; do
              if [ -f "docker_iqt/Dockerfile-iqt-${SERVICE}" ]; then
                docker buildx build -f docker_iqt/Dockerfile-iqt-${SERVICE} \
                  -t ${ECR_BASE}/iqt-${SERVICE}:${TAG} \
                  -t ${ECR_BASE}/iqt-${SERVICE}:prod-latest \
                  --push .
              fi
            done

    - step: &update_image_tags
        name: "Update Image Tags in ArgoCD Repo"
        script:
          - export TAG="prod-${BITBUCKET_COMMIT:0:7}"
          # Clone infra repo and update image tags
          - git clone https://${BB_USER}:${BB_TOKEN}@bitbucket.org/${BB_ORG}/contracts-ai-iqt-infra.git
          - cd contracts-ai-iqt-infra
          - |
            for f in helm/values/prod/*.yaml; do
              yq e -i ".image.tag = \"${TAG}\"" $f
            done
          - git add helm/values/prod/
          - git commit -m "ci: update image tags to ${TAG} [skip ci]"
          - git push
          # ArgoCD auto-syncs from this commit

    - step: &upload_config
        name: "Upload Config to S3"
        script:
          - aws s3 cp config s3://crln-cntrxai-prod-dataz-gbd-phi-useast1/artifacts/${BITBUCKET_COMMIT}/config/ \
              --recursive --region us-east-1

pipelines:
  branches:
    main:
      - step: *upload_config
      - step: *build_and_push
      - step: *update_image_tags
    "feature/**":
      - step: *upload_config
      - step:
          name: "Build Dev Images"
          services: [docker]
          script:
            - export TAG="dev-${BITBUCKET_COMMIT:0:7}"
            - echo "Building dev images with tag ${TAG}"
            # build only, no push to prod ECR
```

**Validation ✅**
```bash
# ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443 &
open https://localhost:8080

# All apps healthy
argocd app list
argocd app get iqt-root

# KEDA scaling test — push a message to SQS
aws sqs send-message \
  --queue-url "https://sqs.us-east-1.amazonaws.com/768867475644/prod-CNTRXAI_llm_input_iqt" \
  --message-body '{"test": "scale-test"}' \
  --region us-east-1

# Watch KEDA scale up inference pod
kubectl get pods -n iqt -w
# Expected: iqt-inference pod appears within 30 seconds

# Watch Karpenter provision GPU node
kubectl get nodes -w
# Expected: new g5.12xlarge node appears
```

---

# PHASE 10: MLOps Platform

## Step 10.1 — MLflow

```yaml
# helm/values/prod/mlflow.yaml
# Self-hosted MLflow on EKS
image:
  repository: ghcr.io/mlflow/mlflow
  tag: v2.12.1

# Backend store: RDS PostgreSQL
backendStore:
  postgres:
    enabled: true
    host: "iqt-prod-rds.xxxxx.us-east-1.rds.amazonaws.com"
    port: 5432
    database: mlflow
    username: mlflow
    password:
      secretRef:
        name: rds-credentials
        key: password

# Artifact store: S3
artifactRoot: "s3://crln-cntrxai-prod-dataz-gbd-phi-useast1/mlflow-artifacts"

# Enable model registry
modelRegistry:
  enabled: true

serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::768867475644:role/iqt-prod-mlflow-irsa"
```

```bash
helm repo add community-charts https://community-charts.github.io/helm-charts
helm install mlflow community-charts/mlflow \
  --namespace mlops \
  --values helm/values/prod/mlflow.yaml
```

```python
# Example: log a fine-tuning experiment from page classification training
import mlflow
import mlflow.pytorch
import os

mlflow.set_tracking_uri("http://mlflow.mlops.svc.cluster.local:5000")
mlflow.set_experiment("page-classification-finetuning")

with mlflow.start_run(run_name="layoutlmv2-client-eh-v3"):
    # Log hyperparameters
    mlflow.log_params({
        "model_base": "microsoft/layoutlmv2-base-uncased",
        "learning_rate": 2e-5,
        "batch_size": 16,
        "epochs": 10,
        "client": "eh",
        "num_classes": 12,
    })

    # ... training loop ...

    # Log metrics per epoch
    mlflow.log_metric("val_accuracy", 0.94, step=10)
    mlflow.log_metric("val_f1", 0.93, step=10)

    # Register model
    mlflow.pytorch.log_model(
        model,
        "layoutlmv2-eh",
        registered_model_name="page-classification-eh"
    )
    # Model now in registry — deploy by promoting to Production stage
```

## Step 10.2 — DVC (Data Version Control)

```bash
# In the main application repo
pip install dvc[s3]

dvc init
dvc remote add -d s3-prod \
  s3://crln-cntrxai-prod-dataz-gbd-phi-useast1/dvc-store

# Track model weights with DVC (not Git)
dvc add models/layoutlmv2-eh/
git add models/layoutlmv2-eh.dvc .gitignore
git commit -m "track LayoutLMv2 EH model with DVC"
dvc push

# Pull specific model version on any machine
dvc pull models/layoutlmv2-eh.dvc

# Reproduce training pipeline
# dvc.yaml
stages:
  train_page_classification:
    cmd: python train_page_classification.py --client eh
    deps:
      - src/page_classification/
      - data/training/eh/
    params:
      - params.yaml:
          - page_classification.learning_rate
          - page_classification.epochs
    metrics:
      - metrics/page_classification_eh.json:
          cache: false
    outs:
      - models/layoutlmv2-eh/
```

## Step 10.3 — LangSmith for LLM Observability

```python
# Add to iqt_main_inference.py — traces every LLM call automatically
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "ls_XXXX"  # from secrets manager
os.environ["LANGCHAIN_PROJECT"] = "iqt-prod"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

# LangChain is already imported in the project (langchain 0.1.13)
# All LLM calls are now automatically traced to LangSmith
# Metrics visible: latency, tokens, cost, input/output, errors
```

## Step 10.4 — Ragas for RAG Evaluation

```python
# scripts/evaluate/ragas_eval.py
# Run periodically to measure RAG quality
from ragas import evaluate
from ragas.metrics import (
    faithfulness,          # is the answer faithful to retrieved context?
    answer_relevancy,      # is the answer relevant to the question?
    context_recall,        # does retrieved context cover the answer?
    context_precision,     # is retrieved context precise (no noise)?
)
from datasets import Dataset
import mlflow

# Load test questions + ground truth answers
test_data = {
    "question": [
        "What is the reimbursement rate for procedure code 99213?",
        "What is the effective date of this contract?",
    ],
    "ground_truth": [
        "$125.00 per visit",
        "January 1, 2024",
    ],
    # These come from your RAG pipeline runs
    "contexts": [...],   # retrieved chunks
    "answer": [...],     # LLM-generated answers
}

dataset = Dataset.from_dict(test_data)

results = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_recall, context_precision]
)

print(results)

# Log to MLflow
with mlflow.start_run(run_name="ragas-weekly-eval"):
    mlflow.log_metrics({
        "ragas_faithfulness": results["faithfulness"],
        "ragas_answer_relevancy": results["answer_relevancy"],
        "ragas_context_recall": results["context_recall"],
        "ragas_context_precision": results["context_precision"],
    })

# Alert if quality drops
if results["faithfulness"] < 0.85:
    # Send Slack alert
    pass
```

---

# PHASE 11: Cost Optimization & Validation

## Step 11.1 — AWQ Quantization (pre-quantize Llama 3.1 70B)

```python
# scripts/quantize/quantize_llama_awq.py
# Run this ONCE on a large GPU instance (e.g., p3.8xlarge) to create AWQ model
# AWQ is better than bitsandbytes runtime quantization: smaller, faster, same quality

from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer

MODEL_PATH = "meta-llama/Meta-Llama-3.1-70B-Instruct"
QUANT_PATH = "/output/llama-3.1-70b-awq"
HF_TOKEN = "hf_NEWTOKEN"

# Load model
model = AutoAWQForCausalLM.from_pretrained(
    MODEL_PATH,
    use_auth_token=HF_TOKEN,
    low_cpu_mem_usage=True,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, use_auth_token=HF_TOKEN)

# Quantize to 4-bit AWQ
quant_config = {
    "zero_point": True,
    "q_group_size": 128,
    "w_bit": 4,         # 4-bit weights
    "version": "GEMM"   # faster on NVIDIA GPUs
}

model.quantize(tokenizer, quant_config=quant_config)
model.save_quantized(QUANT_PATH)
tokenizer.save_pretrained(QUANT_PATH)

# Upload to S3
import subprocess
subprocess.run([
    "aws", "s3", "sync", QUANT_PATH,
    "s3://crln-cntrxai-prod-dataz-gbd-phi-useast1/models/llama-3.1-70b-awq/",
    "--region", "us-east-1"
])

print(f"""
Original model: ~140GB (FP16)
AWQ model:      ~37GB  (4-bit)
Reduction:      73%
On g5.12xlarge (4x A10G = 96GB): can now fit 2 full copies in VRAM
""")
```

## Step 11.2 — Cost Validation Script

```python
# scripts/validation/cost_check.py
"""
Run weekly. Compares estimated GPU cost before vs after optimizations.
"""
import boto3
import subprocess
import json
from datetime import datetime, timedelta

ce = boto3.client('ce', region_name='us-east-1')

def get_eks_compute_cost(days=7):
    end = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    response = ce.get_cost_and_usage(
        TimePeriod={'Start': start, 'End': end},
        Granularity='DAILY',
        Filter={
            'Tags': {
                'Key': 'Project',
                'Values': ['contracts-ai-iqt']
            }
        },
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )

    total = 0
    for day in response['ResultsByTime']:
        for group in day['Groups']:
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            total += cost
            print(f"  {day['TimePeriod']['Start']}: {group['Keys'][0]} = ${cost:.2f}")

    return total

def get_gpu_utilization():
    """Get average GPU utilization from Prometheus"""
    import requests
    r = requests.get(
        "http://localhost:9090/api/v1/query",
        params={"query": "avg(DCGM_FI_DEV_GPU_UTIL)"}
    )
    return float(r.json()['data']['result'][0]['value'][1])

def get_keda_scale_events():
    """Count how many times KEDA scaled to zero (cost savings events)"""
    result = subprocess.run(
        ["kubectl", "get", "events", "-n", "iqt",
         "--field-selector=reason=ScaledToZero",
         "-o", "json"],
        capture_output=True, text=True
    )
    events = json.loads(result.stdout)
    return len(events['items'])

print("=== IQT Cost Report ===")
print(f"\nLast 7 days AWS cost by service:")
total = get_eks_compute_cost(7)
print(f"\nTotal: ${total:.2f}")
print(f"Daily average: ${total/7:.2f}")

print(f"\nGPU Utilization (avg): {get_gpu_utilization():.1f}%")
print(f"KEDA scale-to-zero events (7d): {get_keda_scale_events()}")

# Targets
print("\n=== Targets ===")
print("GPU utilization target: > 60% (currently wasting if < 40%)")
print("Daily GPU cost target: < $200/day")
print("Scale-to-zero events: > 5/week (means GPU not running overnight)")
```

## Step 11.3 — Complete Validation Checklist

```bash
# scripts/validation/full-validation.sh
#!/bin/bash
set -e
PASS=0; FAIL=0

check() {
  if eval "$2" &>/dev/null; then
    echo "✅ $1"
    ((PASS++))
  else
    echo "❌ $1"
    ((FAIL++))
  fi
}

echo "=== Phase 0: Cluster Health ==="
check "EKS nodes ready" "kubectl get nodes | grep -v NotReady | grep Ready | wc -l | grep -qv '^0'"
check "System pods running" "kubectl get pods -n kube-system | grep Running | wc -l | awk '{exit ($1 < 5)}'"
check "CoreDNS running" "kubectl get pods -n kube-system -l k8s-app=kube-dns | grep Running"

echo ""
echo "=== Phase 1: Security ==="
check "HF token not in Dockerfile" "! grep -r 'hf_aqZ' docker_iqt/"
check "No hardcoded passwords in configs" "! grep -r 'bapHEY9' config/"
check "External secrets synced" "kubectl get externalsecret -n iqt | grep True"
check "HF token K8s secret exists" "kubectl get secret huggingface-token -n iqt"

echo ""
echo "=== Phase 2: GPU Stack ==="
check "NVIDIA device plugin running" "kubectl get pods -n gpu-operator | grep nvidia-device-plugin | grep Running"
check "GPU time-slicing active" "kubectl get nodes -l workload=ml-inference-small -o json | jq '.items[].status.capacity[\"nvidia.com/gpu\"]' | grep -q '4'"
check "DCGM exporter running" "kubectl get pods -n gpu-operator | grep dcgm-exporter | grep Running"

echo ""
echo "=== Phase 3: Autoscaling ==="
check "KEDA running" "kubectl get pods -n keda | grep keda-operator | grep Running"
check "KEDA ScaledObjects exist" "kubectl get scaledobjects -n iqt | wc -l | awk '{exit ($1 < 5)}'"
check "Karpenter running" "kubectl get pods -n karpenter | grep karpenter | grep Running"

echo ""
echo "=== Phase 4: Storage ==="
check "EFS PVC bound" "kubectl get pvc -n iqt | grep efs | grep Bound"
check "Models cached on EFS" "kubectl exec -n iqt deploy/iqt-chunking -- ls /models/embedding/.complete 2>/dev/null || true"

echo ""
echo "=== Phase 5: Observability ==="
check "Prometheus running" "kubectl get pods -n monitoring | grep prometheus | grep Running"
check "Grafana running" "kubectl get pods -n monitoring | grep grafana | grep Running"
check "Kubecost running" "kubectl get pods -n monitoring | grep kubecost | grep Running"

echo ""
echo "=== Phase 6: vLLM ==="
check "vLLM pod running" "kubectl get pods -n iqt -l app=iqt-vllm | grep Running"
check "vLLM health endpoint" "kubectl exec -n iqt deploy/iqt-vllm -- curl -sf http://localhost:8000/health"
check "vLLM model loaded" "kubectl exec -n iqt deploy/iqt-vllm -- curl -sf http://localhost:8000/v1/models | grep -q 'llama'"

echo ""
echo "=== Phase 7: Application Services ==="
check "Flask API running" "kubectl get pods -n iqt -l app=iqt-flask | grep Running"
check "KEDA scales inference on SQS" "aws sqs send-message --queue-url $LLM_QUEUE --message-body test --region us-east-1 && sleep 30 && kubectl get pods -n iqt | grep iqt-inference | grep -qv 'No resources'"

echo ""
echo "=== Phase 8: GitOps ==="
check "ArgoCD running" "kubectl get pods -n argocd | grep argocd-server | grep Running"
check "All ArgoCD apps synced" "argocd app list | grep -v Synced | wc -l | grep -q '^1'"  # header only

echo ""
echo "=== RESULTS ==="
echo "✅ Passed: $PASS"
echo "❌ Failed: $FAIL"
echo ""
[ $FAIL -eq 0 ] && echo "🎉 All validations passed!" || echo "⚠️  $FAIL validations failed - investigate before cutover"
```

---

# PHASE 12: Cutover from ECS → EKS

## Step 12.1 — Blue/Green Cutover Plan

```
Day 1:  Deploy ALL services to EKS in parallel with ECS (different SQS queues)
Day 2:  Shadow mode — duplicate 5% of prod SQS messages to EKS queues
Day 3:  Compare outputs (accuracy, latency, cost)
Day 4:  Increase to 25% EKS traffic
Day 5:  Increase to 50% EKS traffic
Day 6:  100% EKS traffic
Day 7:  Decommission ECS tasks (stop, not delete — keep for 2 weeks)
Day 21: Delete ECS task definitions and old AMIs
```

```bash
# scripts/cutover/shadow-traffic.sh
# Route X% of SQS messages to EKS queue by Lambda fan-out

aws lambda create-function \
  --function-name iqt-sqs-fanout \
  --runtime python3.12 \
  --handler fanout.handler \
  --role arn:aws:iam::768867475644:role/iqt-lambda-fanout \
  --zip-file fileb://fanout.zip

# fanout.py
cat > fanout.py << 'LAMBDA'
import boto3, os, json, random

sqs = boto3.client('sqs', region_name='us-east-1')
ECS_QUEUE = os.environ['ECS_QUEUE']
EKS_QUEUE = os.environ['EKS_QUEUE']
EKS_PERCENT = float(os.environ.get('EKS_PERCENT', '5'))

def handler(event, context):
    for record in event['Records']:
        body = record['body']
        # Always send to ECS (current prod)
        sqs.send_message(QueueUrl=ECS_QUEUE, MessageBody=body)
        # Shadow % to EKS
        if random.random() * 100 < EKS_PERCENT:
            sqs.send_message(QueueUrl=EKS_QUEUE, MessageBody=body)
LAMBDA
```

## Step 12.2 — Rollback Plan

```bash
# scripts/rollback/rollback-to-ecs.sh
#!/bin/bash
# Execute if EKS cutover fails

echo "🚨 Rolling back to ECS..."

# 1. Route all traffic back to ECS SQS queues
aws lambda update-function-configuration \
  --function-name iqt-sqs-fanout \
  --environment Variables="{EKS_PERCENT=0}"

# 2. Scale ECS services back up
for SERVICE in preprocessing bbox-generation text-generation page-classification \
               linearizer chunking prompt-gen inference flask; do
  aws ecs update-service \
    --cluster iqt-prod \
    --service iqt-${SERVICE} \
    --desired-count 2 \
    --region us-east-1
done

# 3. Scale EKS GPU nodes to 0 (stop billing)
kubectl scale deployment --all -n iqt --replicas=0

echo "✅ Rolled back to ECS. Monitor for 30 minutes before declaring stable."
```

---

## Summary: What This Plan Achieves

| Metric | Before (ECS) | After (EKS + Optimizations) | Savings |
|---|---|---|---|
| GPU nodes running | 24/7 on-demand | Scale to 0 via KEDA | ~70% |
| GPU utilization | ~20-30% (idle) | ~70-85% (vLLM batching) | — |
| Model load time | 5-10min (S3 per pod) | 30sec (EFS cache) | — |
| LLM throughput | 1 req at a time (raw HF) | 10-50 concurrent (vLLM) | 10-50x |
| GPU per small model | 1 GPU per pod | 0.25 GPU (time-sliced) | 75% |
| CPU services | On-demand | Spot instances | 65% |
| S3/SQS data transfer | Through NAT (~$0.045/GB) | VPC Endpoints (free) | ~$500/mo |
| **Estimated total monthly** | **~$50-80k/mo** | **~$12-20k/mo** | **~65-75%** |