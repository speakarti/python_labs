# -----------------------------------------------
# Data Sources
# -----------------------------------------------
data "aws_caller_identity" "current" {}

# -----------------------------------------------
# EKS Cluster
# -----------------------------------------------
resource "aws_eks_cluster" "eks_np01" {
  name     = "eks-np01"
  version  = "1.35"
  role_arn = "arn:aws:iam::744958734165:role/eks-np01-cluster-role"
  bootstrap_self_managed_addons = false

  vpc_config {
    subnet_ids = [
      "subnet-0bd74ddf24ebf9730",
      "subnet-038c7766f3576a8db",
      "subnet-0d0a8a9146a421f07",
      "subnet-0258b00a7ba670609"
    ]
    # cluster_security_group_id = "sg-0e1ab16f638ccc262"
    endpoint_private_access   = true
    endpoint_public_access    = true
    public_access_cidrs       = ["0.0.0.0/0"]
  }

  kubernetes_network_config {
    service_ipv4_cidr = "172.20.0.0/16"
    ip_family         = "ipv4"
  }

  enabled_cluster_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]

  access_config {
    authentication_mode                         = "API"
    bootstrap_cluster_creator_admin_permissions = true
  }

  upgrade_policy {
    support_type = "EXTENDED"
  }

  tags = {}
}

# -----------------------------------------------
# Admin Access Entries — survives destroy/recreate
# -----------------------------------------------
resource "aws_eks_access_entry" "admins" {
  for_each      = toset(var.cluster_admin_arns)
  cluster_name  = aws_eks_cluster.eks_np01.name
  principal_arn = each.value
  type          = "STANDARD"
  depends_on    = [aws_eks_cluster.eks_np01]
}

resource "aws_eks_access_policy_association" "admins" {
  for_each      = toset(var.cluster_admin_arns)
  cluster_name  = aws_eks_cluster.eks_np01.name
  principal_arn = each.value
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
  access_scope {
    type = "cluster"
  }
  depends_on = [aws_eks_access_entry.admins]
}

# -----------------------------------------------
# Bootstrap Node Group
# -----------------------------------------------
resource "aws_eks_node_group" "bootstrap" {
  cluster_name    = aws_eks_cluster.eks_np01.name
  node_group_name = "eks-np01-bootstrap"
  node_role_arn   = "arn:aws:iam::744958734165:role/eks-np01-bootstrap-node-role"
  version         = "1.35"

  subnet_ids = [
    #"subnet-038c7766f3576a8db",  # ← PRIVATE, goes via TGW
    #"subnet-0bd74ddf24ebf9730"   # ← PRIVATE, goes via TGW
    "subnet-0d0a8a9146a421f07",   # ← PUBLIC, goes via IGW, internet works
    "subnet-0258b00a7ba670609"    # ← PUBLIC, goes via IGW, internet works    
  ]

  capacity_type  = "ON_DEMAND"
  instance_types = ["t3.medium"]
  ami_type       = "AL2023_x86_64_STANDARD"
  disk_size      = 20

  scaling_config {
    min_size     = 1
    max_size     = 2
    desired_size = 1
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    bootstrap = "true"
  }

#  taint {
#    key    = "bootstrap"
#    value  = "true"
#    effect = "NO_SCHEDULE"
#  }

  tags = {
    "kubernetes.io/cluster/eks-np01" = "owned"
    "Name"                           = "eks-np01-bootstrap-ng"
  }

  depends_on = [aws_eks_cluster.eks_np01]
}