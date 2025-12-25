# ===================================================================
# SECURITY POLICY: CI/CD RUNNER
# Principle: Least Privilege
# ===================================================================

# Rule 1: Static Application Secrets (KV Engine)
# Allow ONLY read access to secrets stored under the specific path
# 'secret/data/ci-runner/'.
path "secret/data/ci-runner/*" {
  capabilities = ["read"]
}

# Rule 2: Dynamic Database Credentials (PostgreSQL Engine)
# Allows the runner to request new credentials from the 'readonly-role'
# recipe configured in the database engine.
path "database/creds/readonly-role" {
  capabilities = ["read"]
}

# Rule 3: Explicitly deny access to everything else.
# Vault has a "deny-by-default" policy, so this serves as
# defensive documentation and global safety net.
path "*" {
  capabilities = ["deny"]
}

# ===================================================================
# End of policy
# ===================================================================