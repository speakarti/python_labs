# -----------------------------------------------
# Namespaces
# -----------------------------------------------
resource "kubernetes_namespace_v1" "namespaces" {
  for_each = toset([
    "app",
    "monitoring",
    "istio-system",
    "karpenter",
    "vault",
    "kafka",
    "cert-manager",
    "argocd",
    "kyverno"
  ])

  metadata {
    name = each.value
    labels = {
      "managed-by" = "terraform"
      "env"        = var.environment
    }
  }
}

# -----------------------------------------------
# ClusterRoles
# -----------------------------------------------
resource "kubernetes_cluster_role_v1" "readonly" {
  metadata { name = "eks-readonly" }
  rule {
    api_groups = [""]
    resources  = ["pods","services","configmaps","endpoints","nodes"]
    verbs      = ["get","list","watch"]
  }
  rule {
    api_groups = ["apps"]
    resources  = ["deployments","replicasets","statefulsets","daemonsets"]
    verbs      = ["get","list","watch"]
  }
}

resource "kubernetes_cluster_role_v1" "developer" {
  metadata { name = "eks-developer" }
  rule {
    api_groups = ["","apps"]
    resources  = ["pods","deployments","services","configmaps","replicasets"]
    verbs      = ["get","list","watch","create","update","patch"]
  }
  rule {
    api_groups = [""]
    resources  = ["pods/log","pods/exec","pods/portforward"]
    verbs      = ["get","list","create"]
  }
}

resource "kubernetes_cluster_role_v1" "admin" {
  metadata { name = "eks-admin" }
  rule {
    api_groups = ["*"]
    resources  = ["*"]
    verbs      = ["*"]
  }
}

# -----------------------------------------------
# RoleBindings — bind roles to groups per namespace
# -----------------------------------------------
resource "kubernetes_role_binding_v1" "app_developer" {
  metadata {
    name      = "developer-binding"
    namespace = "app"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role_v1.developer.metadata[0].name
  }
  subject {
    kind      = "Group"
    name      = "developers"
    api_group = "rbac.authorization.k8s.io"
  }
  depends_on = [kubernetes_namespace_v1.namespaces]
}

resource "kubernetes_role_binding_v1" "app_readonly" {
  metadata {
    name      = "readonly-binding"
    namespace = "app"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role_v1.readonly.metadata[0].name
  }
  subject {
    kind      = "Group"
    name      = "viewers"
    api_group = "rbac.authorization.k8s.io"
  }
  depends_on = [kubernetes_namespace_v1.namespaces]
}

# -----------------------------------------------
# ServiceAccounts
# -----------------------------------------------
resource "kubernetes_service_account_v1" "app_sa" {
  metadata {
    name      = "app-service-account"
    namespace = "app"
    labels = {
      "managed-by" = "terraform"
    }
  }
  depends_on = [kubernetes_namespace_v1.namespaces]
}
