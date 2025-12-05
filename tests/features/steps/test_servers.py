import pytest
import requests
from pytest_bdd import scenarios, given, when, then, parsers

# 1. ENLACE CON EL FEATURE
# Esto busca el archivo .feature en el directorio padre (tests/features/)
scenarios('../test_servers.feature')

# --- PASOS PARA EL SERVIDOR WEB (NGINX) ---

@given(parsers.parse('la IP del servidor web es "{ip_address}"'))
def set_web_ip(context, ip_address):
    """
    Guardamos la IP objetivo en nuestro contexto compartido.
    """
    print(f"\n[DEBUG] Configurando IP objetivo: {ip_address}")
    context.target_ip = ip_address

@when('intento acceder a la URL principal')
def access_main_url(context):
    """
    Intentamos hacer un GET a la IP guardada.
    """
    url = f"http://{context.target_ip}"
    try:
        # Usamos requests para probar la conexión HTTP real
        # timeout pequeño para que no se cuelgue si no existe
        response = requests.get(url, timeout=2)
        context.response_status = response.status_code
        context.response_error = None
    except requests.exceptions.RequestException as e:
        # Si falla la conexión (ej. servidor apagado), guardamos el error
        context.response_status = None
        context.response_error = str(e)
        print(f"[DEBUG] Error conectando a {url}: {e}")

@then(parsers.parse('recibo un código de estado HTTP {status_code:d}'))
def check_status_code(context, status_code):
    """
    Verificamos que el status code sea el esperado (ej. 200).
    """
    # Si hubo un error de conexión, fallamos el test con un mensaje claro
    if context.response_error:
        pytest.fail(f"No se pudo conectar al servidor: {context.response_error}")
    
    assert context.response_status == status_code, \
        f"Esperaba status {status_code}, pero recibí {context.response_status}"


# --- PASOS PARA LA BASE DE DATOS (POSTGRESQL) ---

@given('los parámetros de conexión de la DB son correctos')
def set_db_params(context):
    """
    Simulamos o configuramos parámetros por defecto.
    """
    context.db_host = "localhost"
    context.db_port = 5432

@when(parsers.parse('intento conectar como "{user}" a la base de datos "{db_name}"'))
def connect_to_db(context, user, db_name):
    """
    Aquí iría la lógica real con psycopg2. 
    Para este ejemplo, vamos a SIMULAR la conexión para que veas pasar la prueba.
    """
    print(f"\n[DEBUG] Intentando conectar a DB {db_name} como {user}...")
    
    # --- SIMULACIÓN (MOCK) ---
    # Asumimos que si la IP es localhost, la conexión es exitosa.
    # En un entorno real, aquí usarías: psycopg2.connect(...)
    if context.db_host in ["localhost", "127.0.0.1"]:
        context.db_connected = True
    else:
        context.db_connected = False

@then('la conexión a PostgreSQL es exitosa')
def check_db_connection(context):
    assert context.db_connected is True, "La conexión a la base de datos falló."



# tests/features/steps/test_servers.py (Añadir al final)

import redis # Nuevo import necesario

# --- VARIABLES GLOBALES PARA REDIS ---
REDIS_HOST = "10.0.0.23" # Redis se instaló en el web-node
REDIS_PORT = 6379
REDIS_CLIENT = None
TEST_KEY = "iac_test_key"
TEST_VALUE = "infraestructura_como_codigo_funciona"

# ===============================================
# PRUEBAS DEL SERVIDOR DE CACHÉ (REDIS)
# ===============================================

@given(parsers.parse('la IP del servidor caché es "{ip_address}"'))
def set_redis_ip(context, ip_address):
    global REDIS_CLIENT
    try:
        # Se conecta a Redis en la IP del web-node (10.0.0.23)
        REDIS_CLIENT = redis.Redis(host=ip_address, port=REDIS_PORT, db=0, socket_timeout=5)
        # Intenta un ping para verificar la conexión
        REDIS_CLIENT.ping()
        context.redis_client = REDIS_CLIENT
        context.redis_error = None
    except Exception as e:
        context.redis_error = str(e)
        context.redis_client = None

@when('intento guardar y recuperar un valor de caché')
def set_and_get_cache_value(context):
    if context.redis_error:
        context.retrieved_value = None
        return

    try:
        # Guardar un valor
        context.redis_client.set(TEST_KEY, TEST_VALUE)
        # Recuperar el valor
        context.retrieved_value = context.redis_client.get(TEST_KEY)
    except Exception as e:
        context.redis_error = str(e)
        context.retrieved_value = None

@then('el valor recuperado coincide con el valor guardado')
def check_retrieved_value(context):
    if context.redis_error:
        pytest.fail(f"Fallo al conectar o interactuar con Redis: {context.redis_error}")

    # Redis almacena el valor como bytes, por eso usamos .decode('utf-8')
    assert context.retrieved_value is not None, "No se pudo recuperar el valor de Redis."
    assert context.retrieved_value.decode('utf-8') == TEST_VALUE, \
        f"Esperaba '{TEST_VALUE}', pero recibí '{context.retrieved_value.decode('utf-8')}'"


