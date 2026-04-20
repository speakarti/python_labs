terraform {
  backend "s3" {
    bucket         = "eks-np01-tfstate-744958734165"
    key            = "eks-np01/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "eks-np01-tf-lock"
    encrypt        = true
  }
}