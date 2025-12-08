Feature: Servicios de Base de Datos y Cache

  # PostgreSQL
  Scenario: Verificación de Conexión a PostgreSQL
    Given los parámetros de conexión a PostgreSQL
    When intento establecer una conexión con la base de datos
    Then la conexión debe ser exitosa

  # Redis
  Scenario: Verificación de Conexión y Funcionalidad de Redis
    Given los parámetros de conexión a Redis
    When intento establecer la conexión y ejecutar el comando PING
    Then el comando PING debe responder con "PONG"