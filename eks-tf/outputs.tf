output "cluster_name" {
  value = aws_eks_cluster.eks_np01.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.eks_np01.endpoint
}

output "cluster_arn" {
  value = aws_eks_cluster.eks_np01.arn
}

output "oidc_issuer" {
  value = aws_eks_cluster.eks_np01.identity[0].oidc[0].issuer
}

output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --region us-east-1 --name ${aws_eks_cluster.eks_np01.name}"
}

output "node_group_status" {
  value = aws_eks_node_group.bootstrap.status
}