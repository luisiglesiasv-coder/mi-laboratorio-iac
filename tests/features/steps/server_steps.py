# tests/features/steps/server_steps.py

import requests
import psycopg2
import redis
from behave import given, when, then
from behave.runner import Context
import pytest

# --- CONFIGURACIÓN (Ajustar si es necesario) ---
# En un entorno real, estos serían variables de entorno o configuraciones de Pytest/Conftest
POSTGRES_HOST = '10.0.0.31' 
POSTGRES_DB = 'postgres'
POSTGRES_USER = 'postgres'
# NOTA: La contraseña DEBE ser la que usaste en Ansible y Vault
POSTGRES_PASSWORD = 'secure_password_123' 
REDIS_HOST = '10.0.0.31'


# --- PASOS DE WEB (Nginx) ---

@given('la dirección del servidor web es "{address}"')
def step_given_web_server_address(context: Context, address: str):
    """Almacena la dirección del servidor web (Nginx)."""
    context.web_address = address
    context.response = None

@when('hago una solicitud GET al endpoint principal')
def step_when_make_get_request(context: Context):
    """Intenta hacer una solicitud HTTP GET al servidor web."""
    try:
        context.response = requests.get(context.web_address, timeout=5)
    except requests.exceptions.ConnectionError:
        context.response = None

@then('la respuesta debe ser exitosa (código 200)')
def step_then_response_must_be_200(context: Context):
    """Verifica que Nginx respondió con un código 200 OK."""
    if context.response is None:
        pytest.fail(f"Nginx no es accesible en {context.web_address}. Fallo de conexión.")
        
    assert context.response.status_code == 200, \
        f"Código de estado inesperado: {context.response.status_code}"


# --- PASOS DE BASE DE DATOS (PostgreSQL) ---

@given('los parámetros de conexión a PostgreSQL')
def step_given_postgres_params(context: Context):
    """Configura los parámetros para la conexión a PostgreSQL."""
    context.pg_params = {
        'host': POSTGRES_HOST,
        'database': POSTGRES_DB,
        'user': POSTGRES_USER,
        'password': POSTGRES_PASSWORD
    }
    context.pg_conn = None

@when('intento establecer una conexión con la base de datos')
def step_when_try_postgres_connection(context: Context):
    """Intenta conectar a PostgreSQL."""
    try:
        context.pg_conn = psycopg2.connect(**context.pg_params)
    except Exception as e:
        context.pg_conn = e # Almacena el error si falla


@then('la conexión debe ser exitosa')
def step_then_postgres_connection_successful(context: Context):
    """Verifica si la conexión se estableció correctamente."""
    if isinstance(context.pg_conn, Exception):
        pytest.fail(f"Fallo al conectar a PostgreSQL: {context.pg_conn}")
        
    assert context.pg_conn is not None, "La conexión a PostgreSQL no se pudo establecer."
    context.pg_conn.close() # Cerrar la conexión


# --- PASOS DE CACHE (Redis) ---

@given('los parámetros de conexión a Redis')
def step_given_redis_params(context: Context):
    """Configura los parámetros para la conexión a Redis."""
    context.redis_client = redis.Redis(
        host=REDIS_HOST,
        port=6379,
        decode_responses=True,
        socket_connect_timeout=5
    )
    context.redis_ping_result = None

@when('intento establecer la conexión y ejecutar el comando PING')
def step_when_try_redis_ping(context: Context):
    """Intenta ejecutar el comando PING de Redis."""
    try:
        # El método ping() devuelve True si es exitoso
        context.redis_ping_result = context.redis_client.ping() 
    except Exception as e:
        context.redis_ping_result = str(e) # Almacena el error si falla

@then('el comando PING debe responder con "PONG"')
def step_then_redis_ping_successful(context: Context):
    """Verifica que Redis respondió con PONG (la librería traduce True)."""
    assert context.redis_ping_result is True, \
        f"Redis PING falló. Resultado: {context.redis_ping_result}. ¿Está corriendo Redis?"