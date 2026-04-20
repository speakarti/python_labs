variable "cluster_name" {
  default = "eks-np01"
}

variable "region" {
  default = "us-east-1"
}

variable "account_id" {
  default = "744958734165"
}

variable "cluster_admin_arns" {
  description = "List of IAM ARNs to grant cluster admin access"
  type        = list(string)
  default     = [
    "arn:aws:iam::744958734165:user/hilabs-svc-acc"
  ]
}