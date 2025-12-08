# tests/features/vault.feature

# Feature: Servidor de HashiCorp Vault
# Como administrador de sistemas,
# Quiero asegurar que el servidor de secretos Vault esté correctamente desplegado y accesible,
# Para que el Despliegue Continuo pueda recuperar credenciales de forma segura.

Feature: Servidor de HashiCorp Vault

  Scenario: Verificación de Conectividad Básica de Vault
    Given la dirección del servidor de Vault es "http://10.0.0.31:8200"
    When intento obtener la información de salud del sistema Vault
    Then la conexión debe ser exitosa con un código de estado en el rango 200-503
    And el estado de inicialización de Vault debe ser true
    
  Scenario: Verificación de Estado Sellado (Sellado Inicial)
    # Vault inicia Sellado (Sealed) en modo servidor real.
    Given la dirección del servidor de Vault es "http://10.0.0.31:8200"
    When intento obtener la información de salud del sistema Vault
    Then el estado de sellado de Vault debe ser false