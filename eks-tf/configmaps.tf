# -----------------------------------------------
# App ConfigMap
# -----------------------------------------------
resource "kubernetes_config_map_v1" "app_config" {
  metadata {
    name      = "app-config"
    namespace = "app"
    labels = {
      "managed-by" = "terraform"
      "env"        = var.environment
    }
  }

  data = {
    APP_ENV      = var.environment
    REGION       = var.region
    CLUSTER_NAME = var.cluster_name
    LOG_LEVEL    = "info"
  }

  depends_on = [kubernetes_namespace_v1.namespaces]
}

# -----------------------------------------------
# Feature Flags ConfigMap
# -----------------------------------------------
resource "kubernetes_config_map_v1" "feature_flags" {
  metadata {
    name      = "feature-flags"
    namespace = "app"
    labels = {
      "managed-by" = "terraform"
    }
  }

  data = {
    ENABLE_NEW_UI    = "false"
    ENABLE_DARK_MODE = "true"
    MAINTENANCE_MODE = "false"
  }

  depends_on = [kubernetes_namespace_v1.namespaces]
}
