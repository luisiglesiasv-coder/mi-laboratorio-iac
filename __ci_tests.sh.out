#!/bin/bash
set -euo pipefail # Salir inmediatamente si un comando falla

echo "--- 1. CONFIGURACIÓN INICIAL ---"

# 1.1 Variables de Entorno del Runner-Node (Obtenidas de GitHub Secrets)
VAULT_ADDR="http://10.0.0.31:8200"
# Estos valores son leídos desde los secretos de GitHub (RoleID y SecretID)
ROLE_ID="${VAULT_ROLE_ID}" 
SECRET_ID="${VAULT_SECRET_ID}"

# 1.2 Limpiar cualquier token residual
VAULT_TOKEN=""
export VAULT_TOKEN


echo "--- 2. LOGIN EN VAULT (AppRole) ---"

# 2.1 Autenticación: Usar Role ID y Secret ID para obtener un Token de Sesión temporal
LOGIN_RESPONSE=$(curl -s --request POST \
  --data "{\"role_id\": \"${ROLE_ID}\", \"secret_id\": \"${SECRET_ID}\"}" \
  "${VAULT_ADDR}/v1/auth/approle/login")

# 2.2 Extraer el Token del Runner
RUNNER_TOKEN=$(echo "${LOGIN_RESPONSE}" | jq -r '.auth.client_token')

if [ -z "$RUNNER_TOKEN" ] || [ "$RUNNER_TOKEN" == "null" ]; then
    echo "ERROR: Falló la autenticación AppRole. El token es nulo."
    exit 1
fi

export VAULT_TOKEN="${RUNNER_TOKEN}"
TOKEN_LEASE_DURATION=$(echo "${LOGIN_RESPONSE}" | jq -r '.auth.lease_duration')
echo "SUCCESS: Login exitoso. Token obtenido con duración: ${TOKEN_LEASE_DURATION}s"

# =========================================================================
# 3. OBTENER CREDENCIALES DINÁMICAS
# =========================================================================

echo "--- 3.1 OBTENER CREDENCIALES DE POSTGRESQL ---"

# 3.1.1 Obtener credenciales de PostgreSQL (usando el rol 'runner-role')
PG_CREDS_RESPONSE=$(curl -s -H "X-Vault-Token: ${VAULT_TOKEN}" \
  "${VAULT_ADDR}/v1/database/creds/runner-role")

# 3.1.2 Exportar credenciales de PostgreSQL
export PG_USER=$(echo "${PG_CREDS_RESPONSE}" | jq -r '.data.username')
export PG_PASS=$(echo "${PG_CREDS_RESPONSE}" | jq -r '.data.password')
PG_LEASE_ID=$(echo "${PG_CREDS_RESPONSE}" | jq -r '.lease_id')

if [ -z "$PG_USER" ] || [ "$PG_USER" == "null" ]; then
    echo "ERROR: Falló la obtención de credenciales de PostgreSQL."
    exit 1
fi
echo "Postgres Credenciales obtenidas: Usuario ${PG_USER}"

# -------------------------------------------------------------------------
# NUEVO: Obtener Credenciales de Redis
# -------------------------------------------------------------------------

echo "--- 3.2 OBTENER CREDENCIALES DE REDIS ---"

# 3.2.1 Obtener credenciales de Redis (usando el nuevo rol 'redis-runner-role')
REDIS_CREDS_RESPONSE=$(curl -s -H "X-Vault-Token: ${VAULT_TOKEN}" \
  "${VAULT_ADDR}/v1/database/creds/redis-runner-role")

# 3.2.2 Exportar credenciales de Redis
export REDIS_USER=$(echo "${REDIS_CREDS_RESPONSE}" | jq -r '.data.username')
export REDIS_PASS=$(echo "${REDIS_CREDS_RESPONSE}" | jq -r '.data.password')
REDIS_LEASE_ID=$(echo "${REDIS_CREDS_RESPONSE}" | jq -r '.lease_id')

if [ -z "$REDIS_USER" ] || [ "$REDIS_USER" == "null" ]; then
    echo "ERROR: Falló la obtención de credenciales de Redis."
    exit 1
fi
echo "Redis Credenciales obtenidas: Usuario ${REDIS_USER}"


# =========================================================================
# 4. EJECUTAR PRUEBAS DE APLICACIÓN
# =========================================================================

echo "--- 4. EJECUTANDO PRUEBAS DE INTEGRACIÓN ---"

# En este punto, la aplicación de pruebas debe usar las variables de entorno
# PG_USER, PG_PASS, REDIS_USER, y REDIS_PASS para conectarse a los servicios.

# Ejemplo de cómo se pasarían estas credenciales:
./run_integration_tests.sh \
  --pg-user "$PG_USER" \
  --pg-pass "$PG_PASS" \
  --redis-user "$REDIS_USER" \
  --redis-pass "$REDIS_PASS"

TEST_EXIT_CODE=$?


# =========================================================================
# 5. REVOCACIÓN Y LIMPIEZA
# =========================================================================

echo "--- 5. LIMPIEZA DE TOKENS Y LEASES ---"

# 5.1 Revocar el Lease de las credenciales de PostgreSQL
curl -s --request PUT -H "X-Vault-Token: ${VAULT_TOKEN}" \
  --data "{\"lease_id\": \"${PG_LEASE_ID}\"}" \
  "${VAULT_ADDR}/v1/sys/leases/revoke" > /dev/null
echo "PostgreSQL Lease revocado: ${PG_LEASE_ID}"

# 5.2 Revocar el Lease de las credenciales de Redis
curl -s --request PUT -H "X-Vault-Token: ${VAULT_TOKEN}" \
  --data "{\"lease_id\": \"${REDIS_LEASE_ID}\"}" \
  "${VAULT_ADDR}/v1/sys/leases/revoke" > /dev/null
echo "Redis Lease revocado: ${REDIS_LEASE_ID}"

# 5.3 Revocar el Token de Sesión del Runner
curl -s --request PUT -H "X-Vault-Token: ${VAULT_TOKEN}" \
  "${VAULT_ADDR}/v1/auth/token/revoke-self" > /dev/null
echo "Token del Runner revocado."

# 5.4 Devolver el código de salida de las pruebas
exit $TEST_EXIT_CODE