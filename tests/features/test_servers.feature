# tests/features/test_servers.feature

Feature: Validar la Infraestructura Web y DB

  # Escenario 1: Prueba el Nginx instalado en el web-node
  Scenario: El Servidor Web Nginx está corriendo
    Given la IP del servidor web es "10.0.0.23"
    When intento acceder a la URL principal
    Then recibo un código de estado HTTP 200

  # Escenario 2: Prueba la conexión al PostgreSQL en el db-node
  Scenario: La Base de Datos PostgreSQL es accesible
    Given los parámetros de conexión de la DB son correctos
    When intento conectar como "app_user" a la base de datos "app_db"
    Then la conexión a PostgreSQL es exitosa

  # Escenario 3: Prueba la configuracion de cache redis
  Scenario: El Servidor de Caché Redis es accesible
    Given la IP del servidor caché es "10.0.0.23"
    When intento guardar y recuperar un valor de caché
    Then el valor recuperado coincide con el valor guardado
