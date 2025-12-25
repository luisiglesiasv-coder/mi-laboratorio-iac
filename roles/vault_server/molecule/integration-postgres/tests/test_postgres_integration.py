import pytest
import hvac
import psycopg2
import json
import os
from pytest_bdd import scenario, given, when, then

# --- DYNAMIC PATH LOGIC ---
#  We calculate the path to the JSON file based on the location of this test file
#  Structure: molecule/default/tests/test_vault_bdd.py -> ../../../files/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../../files/vault_init_output.json"))


# Connection Parameters (We use localhost because of the published_ports in molecule.yml)
VAULT_ADDR = "http://localhost:8200"
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "my_app_db"

@pytest.fixture
def vault_client():
    """
    Fixture that initializes the Vault client using the root token
    generated dynamically during the converge.
    """
    if not os.path.exists(TOKEN_PATH):
        pytest.fail(f"ERROR: Credentials file not found in: {TOKEN_PATH}")
        
    with open(TOKEN_PATH, 'r') as f:
        data = json.load(f)
    
    # Initialize hvac with the URL of localhost and the token from the file
    client = hvac.Client(url=VAULT_ADDR, token=data['root_token'])
    return client

# --- BDD SCENARIO---

@scenario('test_postgres_integration.feature', 'Verify dynamic user creation and database access')
def test_vault_postgres_integration():
    """Entry function for Pytest-BDD."""
    pass

@given('Vault is running and the database engine is enabled')
def check_vault_status(vault_client):
    assert vault_client.is_authenticated(), "Vault client could not authenticate"
    mounts = vault_client.sys.list_mounted_secrets_engines()
    assert 'database/' in mounts, "Database secrets engine is not mounted"

@when('I request a new credential for the "readonly-role"', target_fixture="db_creds")
def request_creds(vault_client):
    try:
        # We request dynamic credentials from the PostgreSQL role
        response = vault_client.secrets.database.generate_credentials(
            name='readonly-role',
            mount_point='database'
        )
        return response['data']
    except Exception as e:
        pytest.fail(f"Error generating dynamic credentials: {e}")

@then('Vault should return a valid database username')
def verify_username(db_creds):
    # Verify that the user follows the Vault pattern (v-...)
    username = db_creds['username']
    assert username.startswith('v-'), f"Unexpected username: {username}"
    assert db_creds['password'] is not None

@then('I should be able to connect to "postgres-db" using these credentials')
def verify_db_connection(db_creds):
    """
    Try a real connection to PostgreSQL using the dynamic credentials.
    We use 'localhost' because the port is mapped to the host.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=db_creds['username'],
            password=db_creds['password'],
            connect_timeout=5
        )
        cur = conn.cursor()
        cur.execute('SELECT 1;')
        result = cur.fetchone()
        assert result[0] == 1, "The validation query (SELECT 1) failed"
        cur.close()
        conn.close()
    except Exception as e:
        pytest.fail(f"Failed to connect to PostgreSQL at {DB_HOST}:{DB_PORT} -> {e}")