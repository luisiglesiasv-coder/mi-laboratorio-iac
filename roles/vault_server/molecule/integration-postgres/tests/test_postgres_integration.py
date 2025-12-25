import pytest
import hvac
import psycopg2
import json
import os
from pytest_bdd import scenario, given, when, then

# --- LÓGICA DE RUTAS DINÁMICAS ---
# Calculamos la ruta al JSON basándonos en la ubicación de este archivo de test
# Estructura: molecule/default/tests/test_vault_bdd.py -> ../../../files/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../../files/vault_init_output.json"))


# Parámetros de conexión (Usamos localhost por el published_ports en molecule.yml)
VAULT_ADDR = "http://localhost:8200"
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "my_app_db"

@pytest.fixture
def vault_client():
    """
    Fixture que inicializa el cliente de Vault usando el token root
    generado dinámicamente durante el converge.
    """
    if not os.path.exists(TOKEN_PATH):
        pytest.fail(f"ERROR: No se encontró el archivo de credenciales en: {TOKEN_PATH}")
        
    with open(TOKEN_PATH, 'r') as f:
        data = json.load(f)
    
    # Inicializamos hvac con la URL de localhost y el token del archivo
    client = hvac.Client(url=VAULT_ADDR, token=data['root_token'])
    return client

# --- ESCENARIO BDD ---

@scenario('test_postgres_integration.feature', 'Verify dynamic user creation and database access')
def test_vault_postgres_integration():
    """Función de entrada para Pytest-BDD."""
    pass

@given('Vault is running and the database engine is enabled')
def check_vault_status(vault_client):
    assert vault_client.is_authenticated(), "El cliente de Vault no pudo autenticarse"
    mounts = vault_client.sys.list_mounted_secrets_engines()
    assert 'database/' in mounts, "El motor de base de datos no está montado"

@when('I request a new credential for the "readonly-role"', target_fixture="db_creds")
def request_creds(vault_client):
    try:
        # Solicitamos credenciales dinámicas al rol de PostgreSQL
        response = vault_client.secrets.database.generate_credentials(
            name='readonly-role',
            mount_point='database'
        )
        return response['data']
    except Exception as e:
        pytest.fail(f"Error al generar credenciales dinámicas: {e}")

@then('Vault should return a valid database username')
def verify_username(db_creds):
    # Verificamos que el usuario siga el patrón de Vault (v-...)
    username = db_creds['username']
    assert username.startswith('v-'), f"Nombre de usuario inesperado: {username}"
    assert db_creds['password'] is not None

@then('I should be able to connect to "postgres-db" using these credentials')
def verify_db_connection(db_creds):
    """
    Intenta una conexión real a PostgreSQL usando las credenciales dinámicas.
    Usamos 'localhost' porque el puerto está mapeado al host.
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
        assert result[0] == 1, "La consulta de validación (SELECT 1) falló"
        cur.close()
        conn.close()
    except Exception as e:
        pytest.fail(f"Fallo de conexión a PostgreSQL en {DB_HOST}:{DB_PORT} -> {e}")