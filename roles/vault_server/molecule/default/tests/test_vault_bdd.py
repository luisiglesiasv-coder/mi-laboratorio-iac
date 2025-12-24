import pytest
import hvac
import json
import os
from pytest_bdd import scenario, given, when, then, parsers

# --- ESCENARIOS ---
@scenario('features/vault_health.feature', 'Verify system health and service availability')
def test_system_health(): pass

@scenario('features/vault_health.feature', 'Verify security provisioning (AppRole and Policies)')
def test_provisioning_logic(): pass

# --- FIXTURES ---
@pytest.fixture
def vault_root_token():
    path = "../../files/vault_init_output.json"
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
            return data.get('root_token')
    return None

@pytest.fixture
def vault_client(vault_root_token):
    # Ahora que mapeamos el puerto, localhost:8200 funcionará desde el Mac
    client = hvac.Client(url='http://localhost:8200')
    client.token = vault_root_token
    return client

# --- PASOS: SISTEMA ---
@given('the Vault container is running')
def container_running(host):
    # CORRECCIÓN: Usamos find_command en lugar de get_bin_path
    assert host.find_command("vault") is not None

@when('I check the Vault system status')
def check_status(): pass

@then(parsers.parse('the "{binary}" binary should be installed in the PATH'))
def verify_binary(host, binary):
    # CORRECCIÓN: Comprobación nativa de Testinfra
    assert host.exists(binary)

@then(parsers.parse('the service should be listening on port {port:d}'))
def verify_port(host, port):
    # Esta comprobación se hace DENTRO del contenedor
    assert host.socket(f"tcp://0.0.0.0:{port}").is_listening

# --- PASOS: API ---
@given('the Vault server is initialized and unsealed')
def api_ready(vault_client):
    assert vault_client.sys.is_initialized() is True
    assert vault_client.sys.is_sealed() is False

@when('I query the enabled authentication methods')
def query_auth(): pass

@then(parsers.parse('the "{method}" method should be enabled'))
def verify_approle(vault_client, method):
    auth_methods = vault_client.sys.list_auth_methods()
    assert method in auth_methods['data']

@then(parsers.parse('the policy "{policy_name}" should be present in Vault'))
def verify_policy_present(vault_client, policy_name):
    # Obtenemos la lista de políticas
    policies = vault_client.sys.list_acl_policies()
    
    # CAMBIO CRÍTICO: Vault devuelve la lista en la clave 'keys'
    # Vamos a añadir un print de seguridad por si acaso fallara de nuevo
    print(f"DEBUG: Políticas encontradas: {policies['data']['keys']}")
    
    assert policy_name in policies['data']['keys']