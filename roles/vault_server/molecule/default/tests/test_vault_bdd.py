import pytest
import hvac
import json
import os
from pytest_bdd import scenario, given, when, then, parsers

# --- LÓGICA DE RUTAS DINÁMICAS ---
# Calculamos la ruta al JSON basándonos en la ubicación de este archivo de test
# Estructura: molecule/default/tests/test_vault_bdd.py -> ../../../files/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../../files/vault_init_output.json"))

# --- ESCENARIOS ---
@scenario('features/vault_health.feature', 'Verify system health and service availability')
def test_system_health():
    """Verifica que el binario esté en el PATH y el puerto abierto."""
    pass

@scenario('features/vault_health.feature', 'Verify security provisioning (AppRole and Policies)')
def test_provisioning_logic():
    """Verifica que AppRole y las políticas ACL estén configuradas en la API."""
    pass

# --- FIXTURES ---

@pytest.fixture
def vault_client():
    """Configura el cliente de Vault usando el token generado por Ansible."""
    client = hvac.Client(url='http://localhost:8200')
    
    if not os.path.exists(TOKEN_PATH):
        pytest.fail(f"ERROR CRÍTICO: Token no encontrado en {TOKEN_PATH}. "
                    f"Asegúrate de que la tarea de Ansible 'Save Vault credentials' funcionó.")
    
    with open(TOKEN_PATH, 'r') as f:
        data = json.load(f)
        client.token = data.get('root_token')
    
    if not client.is_authenticated():
        pytest.fail("ERROR: El token existe pero Vault rechazó la autenticación.")
        
    return client

# --- PASOS (STEPS): SISTEMA ---

@given('the Vault container is running')
def container_running(host):
    # Verificamos que el comando vault responda en el contenedor
    assert host.find_command("vault") is not None

@when('I check the Vault system status')
def check_status():
    """Paso descriptivo para BDD."""
    pass

@then(parsers.parse('the "{binary}" binary should be installed in the PATH'))
def verify_binary(host, binary):
    assert host.exists(binary)

@then(parsers.parse('the service should be listening on port {port:d}'))
def verify_port(host, port):
    # Verificamos que el socket esté escuchando en el contenedor
    assert host.socket(f"tcp://0.0.0.0:{port}").is_listening

# --- PASOS (STEPS): API ---

@given('the Vault server is initialized and unsealed')
def api_ready(vault_client):
    assert vault_client.sys.is_initialized() is True
    assert vault_client.sys.is_sealed() is False

@when('I query the enabled authentication methods')
def query_auth():
    """Paso descriptivo para BDD."""
    pass

@then(parsers.parse('the "{method}" method should be enabled'))
def verify_approle(vault_client, method):
    auth_methods = vault_client.sys.list_auth_methods()
    
    # Lógica inteligente: normalizamos el nombre para que siempre termine en una sola '/'
    search_key = method if method.endswith('/') else f"{method}/"
    
    print(f"\n[DEBUG] Buscando método: '{search_key}' en la lista de Vault")
    
    assert search_key in auth_methods['data'], f"No se encontró {search_key} en {list(auth_methods['data'].keys())}"
    
@then(parsers.parse('the policy "{policy_name}" should be present in Vault'))
def verify_policy(vault_client, policy_name):
    # Obtenemos la lista de llaves de las políticas ACL
    policies = vault_client.sys.list_acl_policies()['data']['keys']
    assert policy_name in policies