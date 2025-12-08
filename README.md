Documentación del Proyecto - Fase 0: Planificación y Configuración Inicial del Entorno
Este documento detalla los aspectos relevantes de la configuración inicial del entorno y las herramientas utilizadas, permitiendo la reproducibilidad de la fase de planificación y aprovisionamiento.
1. Planificación de la Arquitectura
Se ha diseñado una arquitectura de tres niveles, con un controlador local (máquina de desarrollo) y varios servidores remotos.
1.1. Especificaciones de Hardware y Software Base
Los equipos utilizados son máquinas virtuales (VMs) o servidores con las siguientes especificaciones mínimas:
Rol del Nodo	Sistema Operativo Base	Especificaciones Mínimas	Servicios Instalados Inicialmente
Controlador (Local)	macOS (Ventura/Sonoma)	8GB RAM, 4 Cores	VS Code, Git, Python 3.11+, Homebrew
Servidor Vault & DB	Ubuntu 22.04 LTS	4GB RAM, 2 Cores	HashiCorp Vault, PostgreSQL
Servidores de Aplicación (x2)	Ubuntu 22.04 LTS	4GB RAM, 2 Cores	Nginx, Redis
1.2. Esquema de Direccionamiento IP
Los servidores remotos operan en una subred privada. El controlador se conecta a ellos a través de un gateway o VPN (no especificado aquí, pero asumido).
Rol del Nodo	Dirección IP	Notas
Servidor Vault & DB	10.0.0.31	Punto central para DB y secretos.
Servidores de Aplicación	10.0.0.32, 10.0.0.33	Direcciones de ejemplo; el controlador se conecta vía Ansible SSH.
2. Configuración del Entorno de Desarrollo Local
Esta sección detalla la configuración de las herramientas de desarrollo en el Controlador Local (macOS).
2.1. Herramientas de Línea de Comandos
Se recomienda el uso de Homebrew para la gestión de paquetes en macOS.
Herramienta	Versión Utilizada	Notas de Instalación
Git	2.4+	Instalado por defecto con Xcode Command Line Tools o Homebrew (brew install git).
Python	3.11.x	Instalado vía Homebrew: brew install python@3.11.
curl / unzip	N/A	Utilidades estándar presentes en macOS.
pip y venv	N/A	Gestionados a través de la instalación de Python.
2.2. Configuración de VS Code y Extensiones
Se configuró Visual Studio Code como IDE principal.
Extensión	ID de Extensión	Propósito
YAML	redhat.vscode-yaml	Validación y linting de archivos YAML (playbooks, ansible.cfg).
Ansible	ansible.ansible	Soporte de sintaxis específico para Ansible.
Python	ms-python.python	Soporte para entornos virtuales (venv) y desarrollo Python.
2.3. Gestión del Control de Versiones (GitHub)
Inicialización del Repositorio: Creación de un repositorio remoto en GitHub.
Configuración Local: Clonación del repositorio en la ruta de trabajo principal: /Users/luis/mi-laboratorio-iac.
Flujo de Trabajo: Uso estándar de git pull, git add, git commit y git push para sincronizar el código IaC.
3. Aprovisionamiento y Configuración Inicial de Servicios Remotos
Los siguientes pasos se realizaron en los servidores remotos (Ubuntu 22.04 LTS) como parte del aprovisionamiento inicial.
3.1. Acceso y Seguridad
Acceso SSH: Configurado utilizando claves SSH para acceso sin contraseña desde el controlador local.
Firewall: ufw configurado para permitir el tráfico necesario (SSH, HTTP/S, PostgreSQL 5432, Vault 8200).
3.2. Servicios Instalados
Comandos de ejemplo para instalación inicial en Ubuntu:
bash
# En el servidor DB/Vault (10.0.0.31)
sudo apt update
sudo apt install -y postgresql unzip curl 

# Instalación de Vault (simplificado)
# (Se asume descarga y movimiento del binario a /usr/local/bin)

# En los servidores de Aplicación (10.0.0.32/33)
sudo apt update
sudo apt install -y nginx redis-server
Use code with caution.

3.3. Estado Inicial Clave del Proyecto
Servicio	Estado Inicial Relevante para IaC
PostgreSQL	Usuario postgres creado con la contraseña inicial PostgreSQL*123.
Vault	Servidor inicializado, unsealed (desbloqueado) y accesible en http://10.0.0.31:8200 con el token root.
Nginx/Redis	Servicios instalados y ejecutándose con configuraciones por defecto.

