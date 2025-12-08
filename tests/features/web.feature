Feature: Servidor Web Nginx

  # Prueba de accesibilidad para el nodo que expone el servicio web
  Scenario: Verificación de Conectividad HTTP de Nginx
    Given la dirección del servidor web es "http://10.0.0.23"
    When hago una solicitud GET al endpoint principal
    Then la respuesta debe ser exitosa (código 200)