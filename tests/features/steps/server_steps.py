import requests
import psycopg2
import redis
import os
from behave import given, when, then
from behave.runner import Context
import pytest

# --- CONFIGURACIÓN ---
# Definimos valores por defecto por si las variables de entorno fallan,
# pero priorizamos siempre lo que viene del Pipeline.

# IP del servidor Web (Nginx)
DEFAULT_WEB_HOST = '10.0.0.23'
WEB_URL = f"http://{os.getenv('WEB_HOST', DEFAULT_WEB_HOST)}"

# IP del servidor de Base de Datos (PostgreSQL y Redis)
DEFAULT_DB_HOST = '10.0.0.31'
DB_HOST_TARGET = os.getenv('DB_HOST', DEFAULT_DB_HOST)
REDIS_HOST_TARGET = os.getenv('REDIS_HOST', DEFAULT_DB_HOST)


# --- PASOS DE WEB (Nginx) ---

@given('la dirección del servidor web es "{address}"')
def step_given_web_server_address(context: Context, address: str):
    # Si el feature file trae una IP hardcoded, la usamos. 
    # Si no, usamos la configurada por variable de entorno.
    if "http" not in address:
        context.target_url = WEB_URL
    else:
        context.target_url = address
    context.response = None

@when('hago una solicitud GET al endpoint principal')
def step_when_make_get_request(context: Context):
    try:
        context.response = requests.get(context.target_url, timeout=5)
    except requests.exceptions.ConnectionError as e:
        context.error = e
        context.response = None

@then('la respuesta debe ser exitosa (código 200)')
def step_then_response_must_be_200(context: Context):
    if context.response is None:
        pytest.fail(f"Fallo de conexión HTTP hacia {context.target_url}. Error: {getattr(context, 'error', 'Desconocido')}")
        
    assert context.response.status_code == 200, \
        f"Código de estado inesperado: {context.response.status_code}"


# --- PASOS DE BASE DE DATOS (PostgreSQL) ---

@given('los parámetros de conexión a PostgreSQL')
def step_given_postgres_params(context: Context):
    """Prepara las credenciales leyendo del entorno."""
    context.db_host = DB_HOST_TARGET
    context.db_user = os.getenv('DB_USER')
    context.db_pass = os.getenv('DB_PASS')
    context.db_name = os.getenv('DB_NAME', 'postgres')

    # Fail fast: Si no hay credenciales, fallamos antes de intentar conectar
    if not context.db_user or not context.db_pass:
        pytest.fail("ERROR CRÍTICO: Variables DB_USER o DB_PASS vacías. Vault no inyectó los secretos.")

@when('intento establecer una conexión con la base de datos')
def step_when_try_postgres_connection(context: Context):
    """Intenta conectar con psycopg2."""
    try:
        context.pg_conn = psycopg2.connect(
            host=context.db_host,
            database=context.db_name,
            user=context.db_user,
            password=context.db_pass,
            connect_timeout=5
        )
        context.pg_error = None
    except Exception as e:
        context.pg_conn = None
        context.pg_error = str(e)

@then('la conexión debe ser exitosa')
def step_then_postgres_connection_successful(context: Context):
    if context.pg_conn is None:
        pytest.fail(f"Falló la conexión a PostgreSQL ({context.db_host}). Error: {context.pg_error}")
    
    # Si llegamos aquí, cerramos la conexión para limpiar
    context.pg_conn.close()


# --- PASOS DE CACHE (Redis) ---

@given('los parámetros de conexión a Redis')
def step_given_redis_params(context: Context):
    """Prepara las credenciales de Redis leyendo del entorno."""
    context.redis_host = REDIS_HOST_TARGET
    context.redis_user = os.getenv('REDIS_USER')
    context.redis_pass = os.getenv('REDIS_PASS')

    # Fail fast
    if not context.redis_user or not context.redis_pass:
        pytest.fail("ERROR CRÍTICO: Variables REDIS_USER o REDIS_PASS vacías. Vault no inyectó los secretos.")

@when('intento establecer la conexión y ejecutar el comando PING')
def step_when_try_redis_ping(context: Context):
    """Crea el cliente de Redis con autenticación y hace ping."""
    try:
        # IMPORTANTE: Aquí pasamos username y password para Vault/ACLs
        client = redis.Redis(
            host=context.redis_host,
            port=6379,
            username=context.redis_user,  # <-- EL CAMBIO CLAVE
            password=context.redis_pass,  # <-- EL CAMBIO CLAVE
            decode_responses=True,
            socket_connect_timeout=5
        )
        context.redis_ping_result = client.ping()
        client.close() # Cerramos socket
        context.redis_error = None
    except Exception as e:
        context.redis_ping_result = False
        context.redis_error = str(e)

@then('el comando PING debe responder con "PONG"')
def step_then_redis_ping_successful(context: Context):
    if context.redis_ping_result is not True:
        pytest.fail(f"Redis PING falló contra {context.redis_host}. Error: {context.redis_error}")
    
    # Si context.redis_ping_result es True, la prueba pasa automáticamente