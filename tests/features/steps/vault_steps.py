# tests/features/steps/vault_steps.py

import requests
import os
import json
import pytest
from behave import given, when, then
from behave.runner import Context

# Códigos válidos: 
# 200 (Active), 429 (Standby/Sealed), 501 (Not Init), 503 (Sealed/Maintenance)
VALID_STATUS_CODES = [200, 429, 501, 503]

@given('la dirección del servidor de Vault es "{address}"')
def step_given_vault_address(context: Context, address: str):
    """
    Establece la dirección base de Vault.
    Si el address es 'ENV', lee la variable de entorno VAULT_ADDR.
    """
    if address == "ENV":
        context.vault_address = os.getenv('VAULT_ADDR', 'http://10.0.0.31:8200')
    else:
        context.vault_address = address
        
    context.response = None
    context.health_data = None

@when('intento obtener la información de salud del sistema Vault')
def step_when_get_health_info(context: Context):
    """Llama al endpoint de salud (/v1/sys/health)."""
    health_url = f"{context.vault_address}/v1/sys/health"
    try:
        # Timeout corto para no bloquear el CI si la red falla
        context.response = requests.get(health_url, timeout=5)
        
        # Intentamos leer el JSON independientemente del código de estado,
        # ya que Vault devuelve JSON incluso en errores 429 o 503.
        try:
            context.health_data = context.response.json()
        except json.JSONDecodeError:
            context.health_data = None
            
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
        context.response = None
        context.health_data = None

@then('la conexión debe ser exitosa con un código de estado en el rango 200-503')
def step_then_connection_successful(context: Context):
    """Verifica conectividad HTTP básica."""
    if context.response is None:
        pytest.fail(f"Fallo crítico: No se pudo conectar a Vault en {context.vault_address}")
        
    assert context.response.status_code in VALID_STATUS_CODES, \
        f"Código de estado inesperado: {context.response.status_code}. Respuesta: {context.response.text}"

@then('el estado de inicialización de Vault debe ser {expected_state}')
def step_then_vault_initialized(context: Context, expected_state: str):
    """Verifica initialized = true/false."""
    expected_bool = expected_state.lower() == 'true'
    
    # Si no hay data pero el código es 501, no está inicializado
    if context.response and context.response.status_code == 501:
        actual_state = False
    elif context.health_data:
        actual_state = context.health_data.get('initialized', False)
    else:
        pytest.fail("No hay datos de salud para verificar inicialización.")

    assert actual_state == expected_bool, \
        f"Fallo Inicialización: Esperaba {expected_bool}, obtuvo {actual_state}"

@then('el estado de sellado de Vault debe ser {expected_state}')
def step_then_vault_sealed(context: Context, expected_state: str):
    """Verifica sealed = true/false."""
    expected_bool = expected_state.lower() == 'true'
    
    if context.health_data:
        actual_state = context.health_data.get('sealed')
    else:
        pytest.fail("No hay datos de salud para verificar estado de sellado.")

    assert actual_state == expected_bool, \
        f"Fallo Estado Sellado: Esperaba {expected_bool}, obtuvo {actual_state}"