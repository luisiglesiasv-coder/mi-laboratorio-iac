# tests/features/vault_secrets.feature

Feature: Servidor de HashiCorp Vault

  Scenario: Verificación de Conectividad Básica de Vault
    # Usamos la IP directa que sabemos que funciona en tu entorno
    Given la dirección del servidor de Vault es "http://10.0.0.31:8200"
    When intento obtener la información de salud del sistema Vault
    Then la conexión debe ser exitosa con un código de estado en el rango 200-503
    And el estado de inicialización de Vault debe ser true
    
  Scenario: Verificación de Estado Sellado (Debe estar Desellado)
    # IMPORTANTE: Como el pipeline ya hizo login con AppRole antes,
    # Vault DEBE estar desellado (sealed: false).
    Given la dirección del servidor de Vault es "http://10.0.0.31:8200"
    When intento obtener la información de salud del sistema Vault
    Then el estado de sellado de Vault debe ser false