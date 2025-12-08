# tests/features/steps/vault_steps.py

import requests
from behave import given, when, then
from behave.runner import Context
import json
import pytest

# Lista de códigos de estado válidos que indica que el servicio Vault está vivo
# 200: Inicializado, Desellado, Sin errores.
# 429: Sellado (Sealed).
# 501: No inicializado.
# 503: Servicio no disponible (ej. error de almacenamiento).
VALID_STATUS_CODES = [200, 429, 501, 503]

@given('la dirección del servidor de Vault es "{address}"')
def step_given_vault_address(context: Context, address: str):
    """Establece la dirección base de Vault."""
    context.vault_address = address
    context.response = None
    context.health_data = None

@when('intento obtener la información de salud del sistema Vault')
def step_when_get_health_info(context: Context):
    """Llama al endpoint de salud (/v1/sys/health) y almacena la respuesta."""
    health_url = f"{context.vault_address}/v1/sys/health"
    try:
        # Timeout bajo para fallar rápidamente si el servicio no está
        context.response = requests.get(health_url, timeout=5)
        
        # Intentar parsear el JSON si la respuesta no es 503 o 501 (que a veces son respuestas vacías)
        if context.response.status_code in [200, 429]:
            context.health_data = context.response.json()
            
    except requests.exceptions.ConnectionError:
        context.response = None
    except json.JSONDecodeError:
        context.health_data = {} # Falla si no es JSON

@then('la conexión debe ser exitosa con un código de estado en el rango 200-503')
def step_then_connection_successful(context: Context):
    """Verifica que la conexión fue posible y el código es válido para Vault."""
    if context.response is None:
        pytest.fail(f"Fallo de conexión: Vault no es accesible en {context.vault_address}")
        
    assert context.response.status_code in VALID_STATUS_CODES, \
        f"Vault respondió con código inesperado: {context.response.status_code}"

@then('el estado de inicialización de Vault debe ser {expected_state}')
def step_then_vault_initialized(context: Context, expected_state: str):
    """Verifica si el campo 'initialized' es True o False."""
    expected_bool = expected_state.lower() == 'true'
    
    # Si el código es 501 (Not Initialized), la respuesta implícita es False
    if context.response and context.response.status_code == 501:
        actual_state = False
    elif context.health_data is not None:
        actual_state = context.health_data.get('initialized')
    else:
        pytest.fail("No se pudo obtener información de salud para verificar la inicialización.")

    assert actual_state == expected_bool, \
        f"Vault Initialization Falló: Esperado {expected_bool}, Obtenido {actual_state}"

@then('el estado de sellado de Vault debe ser {expected_state}')
def step_then_vault_sealed(context: Context, expected_state: str):
    """Verifica si el campo 'sealed' es True o False."""
    expected_bool = expected_state.lower() == 'true'
    
    # El estado 'sealed' es relevante si Vault está inicializado.
    if context.health_data is not None:
        actual_state = context.health_data.get('sealed')
    else:
        pytest.fail("No se pudo obtener información de salud para verificar el estado de sellado.")

    assert actual_state == expected_bool, \
        f"Vault Sealed State Falló: Esperado {expected_bool}, Obtenido {actual_state}"