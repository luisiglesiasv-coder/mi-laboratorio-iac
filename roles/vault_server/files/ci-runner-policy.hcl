# ===================================================================
# SECURITY POLICY: CI/CD RUNNER
# Principle: Least Privilege
# ===================================================================

# Rule 1: Application Secrets Access
# Allow ONLY read access to secrets stored under the specific path
# 'secret/data/ci-runner/'.
#
# NOTE: In KV v2 engines, the actual path to read data includes '/data/'.
# The '*' at the end means "any secret inside this folder".
path "secret/data/ci-runner/*" {
  capabilities = ["read"]
}

# Rule 2 (Optional but recommended): Explicitly deny access to everything else.
# Vault has a "deny-by-default" policy, so this is redundant
# but serves as good visual documentation.
path "*" {
  capabilities = ["deny"]
}

# ===================================================================
# End of policy
# ===================================================================
