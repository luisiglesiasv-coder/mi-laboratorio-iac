# Documentación del Proyecto - Fase 0: Planificación y Configuración Inicial del Entorno
Este documento detalla los aspectos relevantes de la configuración inicial del entorno y las herramientas utilizadas, permitiendo la reproducibilidad de la fase de planificación y aprovisionamiento.

**1. Planificación de la Arquitectura**
  Se ha diseñado una arquitectura de tres niveles, con un controlador local (máquina de desarrollo) y varios servidores remotos.

  1.1. Especificaciones de Hardware y Software Base
    Los equipos utilizados son máquinas virtuales (VMs) o servidores con las siguientes especificaciones mínimas:
   
   | Rol del Nodo	| Sistema Operativo Base |	Especificaciones Mínimas |	Servicios Instalados Inicialmente |
   |:------------- |:---------------------- |:------------------------- |:---------------------------------- |
   | Controlador (Local)	| macOS (Ventura/Sonoma)	| 8GB RAM, 4 Cores	| VS Code, Git, Python 3.11+, Homebrew |  
   | Servidor Vault & DB |	Ubuntu 22.04 LTS |	4GB RAM, 2 Cores	| HashiCorp Vault, PostgreSQL |
   | Servidores de Aplicación (x2) |	Ubuntu 22.04 LTS |	4GB RAM, 2 Cores |	Nginx, Redis |

    
<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/a3bfefa6-d4b9-45f5-9c65-23010328af57" />

  1.2. Esquema de Direccionamiento IP
    Los servidores remotos operan en una subred privada. El controlador se conecta a ellos a través de un gateway o VPN (no especificado aquí, pero asumido).
    
   |Rol del Nodo	| Dirección IP	| Notas|
   |:---|:---|:---|
   | Servidor Vault & DB | 10.0.0.31 | Punto central para DB y secretos. |
   | Servidores de Aplicación |	10.0.0.32, 10.0.0.33	| Direcciones de ejemplo; el controlador se conecta vía Ansible SSH. |
   
    
 **2. Configuración del Entorno de Desarrollo Local**
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




Analizar el flujo de ejecución de la Integración Continua (CI) es esencial para comprender cómo todas las piezas del proyecto (Ansible, Vault, BDD, GitHub Actions) interactúan.

Vamos a desglosar este proceso en tres componentes principales: los Playbooks de Configuración, el Runner Local (nuestro nodo de ejecución), y el Flujo de CI paso a paso.1. 📖 Explicación Previa: Los Playbooks de AnsibleNuestros playbooks son la capa de Infraestructura como Código (IaC). Su propósito es garantizar que la infraestructura de las máquinas remotas esté configurada exactamente como se espera para que las pruebas automáticas puedan ejecutarse.PlaybookPropósito PrincipalFicheros Clave Usadosvault-config.yml🔑 Configura el motor de secretos database/ de Vault, define el role (runner_role) y crea las reglas de política de acceso (runner_policy) para los runners de CI.hosts.ini, Colección community.hashi_vault.db.yml💾 Configura la máquina que aloja PostgreSQL (nodo db-node). Instala el motor de base de datos.hosts.ini, psycopg2-binary (dependencia).web.yml / redis.yml (implícito)🌐 Configura el web-node (o runner-node) instalando servicios de red y caché como Nginx y Redis.hosts.ini.
* Dependencia: Todos los playbooks dependen del archivo hosts.ini para conocer las direcciones IP de los nodos (db-node: 10.0.0.31, runner-node: 10.0.0.23) y del paquete ansible-core y las colecciones necesarias (como community.hashi_vault).

2. ⚙️ Configuración del Runner Node Local
El nodo runner-node (IP: 10.0.0.23, alias web-node) tiene un doble rol en este entorno: aloja servicios de aplicación (Nginx y Redis) y actúa como GitHub Actions Self-Hosted Runner.

Configuración Previa del runner-node:
Software de Base: Debe tener instalado Ubuntu, Python 3 y las herramientas de desarrollo (build-essential).

Servicios: Se utilizan los playbooks (web.yml, redis.yml) para instalar y configurar Nginx (Web Service) y Redis (Cache Service).

GitHub Runner: Se descarga y configura el software de GitHub Actions Runner. Este se ejecuta bajo el usuario luis y escucha las peticiones del repositorio.

Relación de Confianza: El usuario luis está configurado con una relación de confianza basada en claves SSH entre todas las máquinas, permitiendo la ejecución de comandos remotos de Ansible.

. 🚀 Flujo de Ejecución de la Integración Continua (CI)El proceso se define en el workflow bdd_test.yml y se activa con cada git push. El flujo de ejecución es secuencial y crucial para la seguridad:A. Preparación del Entorno (runner-node)PasoAcciónFicheros UsadosPropósito1. Checkout del CódigoClona el repositorio en el workspace del runner.Todos los ficherosAccede a las pruebas y workflows.2. Instalar Vault CLIDescarga e instala el binario de línea de comandos vault.Script de instalación (interno)Necesario para comunicarse con Vault en el siguiente paso.3. Instalar DependenciasEjecuta pip install -r requirements.txt.requirements.txtInstala librerías clave como behave, hvac (cliente de Vault Python) y psycopg2-binary (driver de PostgreSQL) en el venv.B. Consumo de Secretos de Vault (Seguridad)PasoAcciónFicheros UsadosPropósito4. Configurar Credenciales de VaultUsa el VAULT_TOKEN (guardado como secreto de GitHub) para ejecutar vault read -format=json database/creds/runner_role.bdd_test.yml (para la IP de Vault y el token).CRÍTICO: Obtiene el DB_USER y DB_PASS dinámicos. Exporta estas credenciales temporales a variables de entorno (DB_USER, DB_PASS) usando $GITHUB_ENV.C. Ejecución de Pruebas BDDPasoAcciónFicheros UsadosPropósito5. Ejecutar Pruebas BDD BehaveEjecuta ./venv/bin/behave tests/features/.db_data.feature y vault_secrets.featureDefinen el comportamiento esperado del sistema (ej. "dada una conexión, la respuesta debe ser exitosa").server_steps.pyEl código Python que implementa la lógica de los pasos Gherkin. Este archivo lee las credenciales del entorno (os.environ.get('DB_USER')) para conectarse a PostgreSQL.conftest.py (opcional)Configuración de fixtures para las pruebas.6. Post Checkout(Limpieza y Finalización)N/AEl job de CI finaliza.


<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/dd31d3aa-b206-4928-8973-907fedbd090f" />

<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/f841fe79-c4ae-4d7d-a618-f01546b30c03" />


<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/4fd69a87-0374-424a-98fd-6317a2e443d6" />


N.º,Fase y Sistema,Pasos Detallados y Ficheros Involucrados
1. Triger,Tu Máquina Local (MacBook) 💻 → GitHub,Un git commit & git push activa el workflow bdd_test.yml en GitHub Actions.
2. Checkout,Runner-Node (10.0.0.23) 🏃,El Self-Hosted Runner se activa y ejecuta el paso Checkout del Código (actions/checkout@v4) para clonar el repositorio.
3. Configuración,Runner-Node 🛠️,Instalación de Vault CLI: Se ejecuta el script de descarga manual (solución sin sudo) para garantizar que el comando vault esté disponible en el $PATH.
4. Dependencias,Runner-Node 🐍,"Instalar Dependencias de Python: Ejecuta pip install -r requirements.txt. Instala behave, hvac, y psycopg2-binary en el entorno virtual (venv)."
5. Autenticación,Runner-Node ↔ GitHub Secrets 🔑,El workflow accede al VAULT_TOKEN (oculto en los Secretos de GitHub) para autenticarse temporalmente.
6. Secretos Dinámicos,Runner-Node ↔ Vault (10.0.0.31) 🔒,El runner ejecuta vault read database/creds/runner_role (usando el token). Vault genera y devuelve un DB_USER y DB_PASS únicos y temporales.
7. Exportación,Runner-Node 🌐,"Las credenciales temporales se exportan como variables de entorno (DB_USER, DB_PASS) utilizando $GITHUB_ENV, haciéndolas accesibles para el siguiente paso."
8. Ejecución,Runner-Node ✅,Ejecutar Pruebas BDD: Se lanza ./venv/bin/behave tests/features/. Los archivos .feature definen las pruebas. Los archivos server_steps.py leen las variables de entorno (os.environ.get('DB_USER')) para conectarse a PostgreSQL (10.0.0.31) y verificar el estado de Nginx y Redis.
9. Resultado,GitHub 📊,El runner devuelve el resultado (Éxito/Fallo) de las pruebas a GitHub.

   <img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/f5c15b3e-fe6e-4333-be5a-f822213489ab" />



    






Nginx/Redis	Servicios instalados y ejecutándose con configuraciones por defecto.


