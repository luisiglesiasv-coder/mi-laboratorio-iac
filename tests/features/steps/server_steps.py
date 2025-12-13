# tests/features/steps/server_steps.py

import requests
import psycopg2
import redis
import os # <-- ¡Nuevo! Necesario para leer variables de entorno
from behave import given, when, then
from behave.runner import Context
import pytest

# --- CONFIGURACIÓN (Ajustar si es necesario) ---
# Ahora dependemos de variables de entorno (DB_HOST, DB_USER, DB_PASS, DB_NAME)
# Las siguientes constantes SÓLO se usan como valor por defecto si la variable de entorno no existe.
WEB_ADDRESS = 'http://10.0.0.23'
REDIS_HOST = '10.0.0.31'


# --- FUNCIÓN AUXILIAR DE CONEXIÓN A DB (USANDO VAULT SECRETS) ---

def connect_to_db(context: Context, database_name: str):
    """Establece una conexión a PostgreSQL usando credenciales dinámicas de Vault."""
    try:
        # Recuperar credenciales del entorno (establecidas por bdd_test.yml)
        host = os.environ.get('DB_HOST', WEB_ADDRESS) # Fallback al host de la app
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASS')

        if not user or not password:
            pytest.fail("Error: Las variables de entorno DB_USER o DB_PASS no fueron establecidas. ¿Falló Vault?")

        # Intentar la conexión
        context.pg_conn = psycopg2.connect(
            host=host,
            database=database_name,
            user=user,
            password=password
        )
        context.pg_conn.autocommit = True
    except Exception as e:
        # Almacenar el error en el contexto para que el paso 'then' pueda verificarlo
        context.pg_conn = e


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
    """
    Este paso ya no configura solo los parámetros, sino que intenta la conexión 
    usando la función auxiliar y las credenciales dinámicas.
    """
    # Intentamos conectar a la base de datos 'app_db' (nombre común de aplicación)
    # Si quieres probar la conexión al sistema, usa 'postgres'
    connect_to_db(context, database_name='postgres') 

@when('intento establecer una conexión con la base de datos')
def step_when_try_postgres_connection(context: Context):
    """
    Este paso ahora está vacío porque la conexión se intenta en el paso 'given' 
    para poder pasar el estado de la conexión al paso 'then'.
    """
    pass # La lógica fue movida a step_given_postgres_params


@then('la conexión debe ser exitosa')
def step_then_postgres_connection_successful(context: Context):
    """Verifica si la conexión se estableció correctamente."""
    # Si context.pg_conn es una excepción, fallamos
    if isinstance(context.pg_conn, Exception):
        pytest.fail(f"Fallo al conectar a PostgreSQL con credenciales de Vault: {context.pg_conn}")
        
    assert context.pg_conn is not None, "La conexión a PostgreSQL no se pudo establecer."
    
    # Si la conexión es exitosa, la cerramos limpiamente
    if context.pg_conn and not isinstance(context.pg_conn, Exception):
        context.pg_conn.close() 


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