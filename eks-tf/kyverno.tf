# -----------------------------------------------
# Kyverno — Policy Engine
# -----------------------------------------------
resource "helm_release" "kyverno" {
  name             = "kyverno"
  repository       = "https://kyverno.github.io/kyverno"
  chart            = "kyverno"
  namespace        = "kyverno"
  create_namespace = false
  version          = "3.7.1"
  wait             = true
  timeout          = 300

  set {
    name  = "admissionController.replicas"
    value = "1"
  }
  set {
    name  = "backgroundController.enabled"
    value = "true"
  }
  set {
    name  = "cleanupController.enabled"
    value = "true"
  }
  set {
    name  = "reportsController.enabled"
    value = "true"
  }

  depends_on = [
    kubernetes_namespace_v1.namespaces,
    aws_eks_node_group.bootstrap
  ]
}

# -----------------------------------------------
# Policy 1: Require resource limits
# -----------------------------------------------
resource "kubernetes_manifest" "policy_require_limits" {
  manifest = {
    apiVersion = "kyverno.io/v1"
    kind       = "ClusterPolicy"
    metadata = {
      name = "require-resource-limits"
      annotations = {
        "policies.kyverno.io/title"    = "Require Resource Limits"
        "policies.kyverno.io/severity" = "medium"
      }
    }
    spec = {
      validationFailureAction = "Audit"  # Audit first, change to Enforce later
      background              = true
      rules = [{
        name = "check-limits"
        match = {
          any = [{
            resources = {
              kinds = ["Pod"]
            }
          }]
        }
        validate = {
          message = "CPU and memory limits are required"
          pattern = {
            spec = {
              containers = [{
                resources = {
                  limits = {
                    cpu    = "?*"
                    memory = "?*"
                  }
                }
              }]
            }
          }
        }
      }]
    }
  }
  depends_on = [helm_release.kyverno]
}

# -----------------------------------------------
# Policy 2: Disallow latest image tag
# -----------------------------------------------
resource "kubernetes_manifest" "policy_disallow_latest" {
  manifest = {
    apiVersion = "kyverno.io/v1"
    kind       = "ClusterPolicy"
    metadata = {
      name = "disallow-latest-tag"
      annotations = {
        "policies.kyverno.io/title"    = "Disallow Latest Tag"
        "policies.kyverno.io/severity" = "medium"
      }
    }
    spec = {
      validationFailureAction = "Audit"
      background              = true
      rules = [{
        name = "check-image-tag"
        match = {
          any = [{
            resources = {
              kinds = ["Pod"]
            }
          }]
        }
        validate = {
          message = "Image tag :latest is not allowed. Use a specific version."
          pattern = {
            spec = {
              containers = [{
                image = "!*:latest"
              }]
            }
          }
        }
      }]
    }
  }
  depends_on = [helm_release.kyverno]
}

# -----------------------------------------------
# Policy 3: Require pod labels
# -----------------------------------------------
resource "kubernetes_manifest" "policy_require_labels" {
  manifest = {
    apiVersion = "kyverno.io/v1"
    kind       = "ClusterPolicy"
    metadata = {
      name = "require-pod-labels"
      annotations = {
        "policies.kyverno.io/title"    = "Require Pod Labels"
        "policies.kyverno.io/severity" = "low"
      }
    }
    spec = {
      validationFailureAction = "Audit"
      background              = true
      rules = [{
        name = "check-labels"
        match = {
          any = [{
            resources = {
              kinds      = ["Pod"]
              namespaces = ["app"]
            }
          }]
        }
        validate = {
          message = "Labels app, env and team are required on all pods in app namespace"
          pattern = {
            metadata = {
              labels = {
                app  = "?*"
                env  = "?*"
                team = "?*"
              }
            }
          }
        }
      }]
    }
  }
  depends_on = [helm_release.kyverno]
}

# -----------------------------------------------
# Policy 4: Disallow privileged containers
# -----------------------------------------------
resource "kubernetes_manifest" "policy_no_privileged" {
  manifest = {
    apiVersion = "kyverno.io/v1"
    kind       = "ClusterPolicy"
    metadata = {
      name = "disallow-privileged-containers"
      annotations = {
        "policies.kyverno.io/title"    = "Disallow Privileged Containers"
        "policies.kyverno.io/severity" = "high"
      }
    }
    spec = {
      validationFailureAction = "Audit"
      background              = true
      rules = [{
        name = "check-privileged"
        match = {
          any = [{
            resources = {
              kinds = ["Pod"]
            }
          }]
        }
        validate = {
          message = "Privileged containers are not allowed"
          pattern = {
            spec = {
              containers = [{
                "=(securityContext)" = {
                  "=(privileged)" = false
                }
              }]
            }
          }
        }
      }]
    }
  }
  depends_on = [helm_release.kyverno]
}

# -----------------------------------------------
# Policy 5: Auto-add labels (mutation)
# -----------------------------------------------
resource "kubernetes_manifest" "policy_add_labels" {
  manifest = {
    apiVersion = "kyverno.io/v1"
    kind       = "ClusterPolicy"
    metadata = {
      name = "add-default-labels"
    }
    spec = {
      rules = [{
        name = "add-cluster-label"
        match = {
          any = [{
            resources = {
              kinds = ["Pod"]
            }
          }]
        }
        mutate = {
          patchStrategicMerge = {
            metadata = {
              labels = {
                "+managed-by" = "kyverno"
                "+cluster"    = var.cluster_name
              }
            }
          }
        }
      }]
    }
  }
  depends_on = [helm_release.kyverno]
}



# -----------------------------------------------
# Kyverno Policy Library — CIS Benchmark Policies
# -----------------------------------------------

# Check available versions first:
# helm search repo kyverno/kyverno-policies --versions

resource "helm_release" "kyverno_policies" {
  name       = "kyverno-policies"
  repository = "https://kyverno.github.io/kyverno"
  chart      = "kyverno-policies"
  namespace  = "kyverno"
  version    = "3.7.1"  # match kyverno version
  wait       = true
  timeout    = 300

  # -----------------------------------------------
  # Pod Security Standard — choose ONE:
  # baseline    = basic security (recommended start)
  # restricted  = strict security (production)
  # privileged  = no restrictions (dev only)
  # -----------------------------------------------
  set {
    name  = "podSecurityStandard"
    value = "baseline"
  }

  # Set all policies to Audit first
  # Change to Enforce once you verify no violations
  set {
    name  = "validationFailureAction"
    value = "Audit"
  }

  # Background scanning — checks existing resources
  set {
    name  = "background"
    value = "true"
  }

  depends_on = [helm_release.kyverno]
}