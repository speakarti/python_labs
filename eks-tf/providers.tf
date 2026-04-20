terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.82"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 3.1"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }
  required_version = ">= 1.3.0"
}

provider "aws" {
  region = var.region
}

provider "kubernetes" {
  host                   = aws_eks_cluster.eks_np01.endpoint
  cluster_ca_certificate = base64decode(
    aws_eks_cluster.eks_np01.certificate_authority[0].data
  )
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    args        = ["eks", "get-token", "--cluster-name", var.cluster_name]
    command     = "aws"
  }
}

# Add helm provider config
provider "helm" {
  kubernetes {
    host                   = aws_eks_cluster.eks_np01.endpoint
    cluster_ca_certificate = base64decode(
      aws_eks_cluster.eks_np01.certificate_authority[0].data
    )
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      args        = ["eks", "get-token", "--cluster-name", var.cluster_name]
      command     = "aws"
    }
  }
}