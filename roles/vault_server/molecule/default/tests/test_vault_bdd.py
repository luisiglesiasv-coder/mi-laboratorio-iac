import pytest
import hvac
import json
import os
from pytest_bdd import scenario, given, when, then, parsers

# Ruta confirmada por tu comando find
TOKEN_PATH = "/Users/luis/mi-laboratorio-iac/roles/vault_server/files/vault_init_output.json"

@pytest.fixture
def vault_client():
    client = hvac.Client(url='http://localhost:8200')
    if not os.path.exists(TOKEN_PATH):
        pytest.fail(f"Token no encontrado en {TOKEN_PATH}")
    with open(TOKEN_PATH, 'r') as f:
        client.token = json.load(f).get('root_token')
    return client

# --- ESCENARIOS ---
@scenario('features/vault_health.feature', 'Verify system health and service availability')
def test_system_health(): pass

@scenario('features/vault_health.feature', 'Verify security provisioning (AppRole and Policies)')
def test_provisioning_logic(): pass

# --- PASOS ---
@given('the Vault container is running')
def container_running(host):
    assert host.find_command("vault") is not None

@given('the Vault server is initialized and unsealed')
def api_ready(vault_client):
    assert vault_client.sys.is_initialized() and not vault_client.sys.is_sealed()

@when('I check the Vault system status')
def check_status(): pass

@when('I query the enabled authentication methods')
def query_auth(): pass

@then(parsers.parse('the "{binary}" binary should be installed in the PATH'))
def verify_binary(host, binary):
    assert host.exists(binary)

@then(parsers.parse('the service should be listening on port {port:d}'))
def verify_port(host, port):
    assert host.socket(f"tcp://0.0.0.0:{port}").is_listening

@then(parsers.parse('the "{method}" method should be enabled'))
def verify_approle(vault_client, method):
    assert method in vault_client.sys.list_auth_methods()['data']

@then(parsers.parse('the policy "{policy_name}" should be present in Vault'))
def verify_policy(vault_client, policy_name):
    # Obtenemos las llaves de las políticas
    policies = vault_client.sys.list_acl_policies()['data']['keys']
    assert policy_name in policies