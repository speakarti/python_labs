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
  }
  required_version = ">= 1.3.0"
}

provider "aws" {
  region = var.region
}