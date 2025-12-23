import pytest
from pytest_bdd import scenario, given, when, then

@scenario('features/vault_health.feature', 'Verify that the Vault service is operational and configured')
def test_vault_health():
    """BBD entry point"""
    pass

@given('the Vault container is running')
def vault_container_running(host):
    # Verificamos que el proceso vault existe
    assert host.process.get(user="vault")

@when('I check the Vault file system status')
def check_filesystem(host):
    pytest.vault_conf = host.file("/etc/vault.d/vault.hcl")

@then('the "vault" binary should be installed in the PATH')
def verify_binary(host):
    assert host.exists("vault")

@then('the service should be listening on port 8200')
def verify_port(host):
    socket = host.socket("tcp://0.0.0.0:8200")
    assert socket.is_listening