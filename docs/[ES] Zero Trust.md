# Documentación Técnica: Infraestructura como Código (IaC) para Vault Server

Esta documentación describe la arquitectura, la estructura de archivos y la lógica de aprovisionamiento del rol de Ansible desarrollado para la gestión automatizada de **HashiCorp Vault**.

---

## 1. Estructura de Archivos del Proyecto

A continuación se detalla la jerarquía completa del repositorio obtenida mediante la ejecución del comando `tree .`:

```text
.
├── README.md
├── defaults
│   └── main.yml
├── files
│   ├── ci-runner-policy.hcl
│   ├── ci_runner_role_id.txt
│   ├── ci_runner_secret_id.txt
│   └── vault_init_output.json
├── handlers
│   └── main.yml
├── molecule
│   ├── _shared
│   │   └── cleanup.yml
│   ├── default
│   │   ├── converge.yml
│   │   ├── group_vars
│   │   │   └── all.yml
│   │   ├── molecule.yml
│   │   ├── prepare.yml
│   │   ├── tests
│   │   │   ├── conftest.py
│   │   │   ├── features
│   │   │   │   └── vault_health.feature
│   │   │   └── test_vault_bdd.py
│   │   └── verify.yml
│   └── integration-postgres
│       ├── converge.yml
│       ├── group_vars
│       │   └── all.yml
│       ├── molecule.yml
│       └── verify.yml
├── tasks
│   ├── bootstrap.yml
│   ├── install.yml
│   ├── main.yml
│   ├── provision.yml
│   ├── provisioning
│   │   ├── auth
│   │   │   └── approle.yml
│   │   ├── engines
│   │   │   ├── postgresql.yml
│   │   │   └── redis.yml
│   │   ├── policies
│   │   │   └── main.yml
│   │   └── roles
│   │       └── ci-runner.yml
│   └── service.yml
└── templates
    ├── vault.hcl.j2
    └── vault.service.j2
```
## **2. Glosario de Variables (`defaults/main.yml`)**

Estas variables definen el comportamiento del rol y pueden ser sobrescritas según el entorno (producción, staging o desarrollo).

| Variable | Propósito | Ejemplo / Valor |
| :--- | :--- | :--- |
| `**vault_version**` | Versión del binario de HashiCorp Vault a descargar. | `1.15.4` |
| `**vault_addr**` | URL local donde escucha el API de Vault. | `http://127.0.0.1:8200` |
| `**vault_config_dir**` | Directorio donde se almacena el archivo `vault.hcl`. | `/etc/vault.d` |
| `**vault_data_dir**` | Directorio de persistencia para el motor de almacenamiento. | `/opt/vault/data` |
| `**vault_unseal_keys_dir**` | Carpeta en tu Mac donde se guardarán las llaves tras el init. | `{{ role_path }}/files` |
| `**vault_root_token_mem**` | Variable de memoria que captura el Token durante la sesión. | *(Runtime Fact)* |

---

## **3. Descripción de Directorios y Lógica Técnica**

### **📂 Directorio `tasks/`**
Es el motor principal del rol. El flujo de ejecución es el siguiente:
* `**install.yml**`: Gestiona la creación del usuario de sistema `vault`, los grupos y el despliegue del binario.
* `**service.yml**`: Configura el servicio mediante **Systemd**, permitiendo la gestión mediante `systemctl`.
* `**bootstrap.yml**`: Orquestación crítica. Realiza el **Init** y el **Unseal** automático, persistiendo las llaves en el host local.
* `**provision.yml**`: Archivo puente que organiza la configuración lógica (Auth, Engines, Policies).



### **📂 Directorio `tasks/provisioning/`**
Contiene la lógica que utiliza `vault_write` para interactuar con la API (sustituyendo módulos ausentes):
* `**auth/approle.yml**`: Habilita el método de autenticación AppRole.
* `**policies/main.yml**`: Lee archivos `.hcl` locales y los registra como políticas de seguridad.
* `**roles/ci-runner.yml**`: Configura los roles específicos y exporta el **RoleID** y **SecretID**.

### **📂 Directorio `files/`**
Repositorio de artefactos resultantes y estáticos:
* `**ci-runner-policy.hcl**`: Definición de permisos de acceso.
* `**vault_init_output.json**`: JSON con las llaves maestras generadas en el primer arranque.
* `**ci_runner_role_id.txt**`: ID de cliente extraído para el uso de servicios externos.
* `**ci_runner_secret_id.txt**`: Secreto de cliente extraído para el uso de servicios externos.

### **📂 Directorio `molecule/`**
Configuración del escenario de pruebas unitarias:
* `**prepare.yml**`: Tarea encargada de instalar `hvac` (librería de Python) dentro del contenedor Docker para habilitar la comunicación con Vault.
* `**default/tests/**`: Contiene pruebas BDD (Gherkin) para validar que el aprovisionamiento cumple con los requisitos de negocio.



---

## **4. Flujo de Ejecución de la Pipeline (Orden Lógico)**

1.  **Levantamiento de Infraestructura**: Molecule inicia el contenedor Docker basado en Ubuntu.
2.  **Preparación del Nodo**: Se ejecuta el `prepare.yml` para instalar dependencias de Python (`pip`, `hvac`).
3.  **Convergencia del Rol**:
    * **Instalación**: Configuración de binarios y permisos.
    * **Bootstrap**: Inicialización y desbloqueo (Unseal) del servidor.
    * **Provisioning**: Configuración de la API (AppRole y ACLs).
4.  **Extracción de Secretos**: Los IDs generados se envían desde el contenedor hacia la carpeta `files/` del Mac.
5.  **Verificación**: Se ejecutan los tests de Molecule para confirmar que el puerto 8200 responde y que las políticas están activas.

---

> **⚠️ NOTA DE SEGURIDAD**: Los archivos generados en `roles/vault_server/files/` contienen secretos en texto plano. Se recomienda encarecidamente añadirlos al `.gitignore` o cifrarlos con **Ansible Vault** antes de subirlos a un repositorio remoto.


---

## **2. Desglose de Directorios y Propósitos**

### **📁 `defaults/`**
* **`main.yml`**: Define las variables base del rol (versiones, rutas de instalación, puertos). Es el punto de entrada para personalizar el despliegue sin modificar el código fuente.

### **📁 `files/` (Artefactos y Persistencia)**
Contiene los objetos que Ansible intercambia entre el Mac y el contenedor:
* **`ci-runner-policy.hcl`**: Definición de permisos en lenguaje HCL de HashiCorp.
* **`vault_init_output.json`**: Generado dinámicamente durante el *Bootstrap*. Contiene las llaves maestras y el Root Token.
* **`ci_runner_role_id.txt` / `ci_runner_secret_id.txt`**: Credenciales finales extraídas de Vault para el uso de servicios externos (CI/CD).

### **📁 `tasks/` (Lógica Procedural)**
El archivo **`main.yml`** orquestra el ciclo de vida en el siguiente orden:
1.  **`install.yml`**: Instalación de binarios y gestión de usuarios/permisos.
2.  **`service.yml`**: Configuración de la unidad de Systemd y arranque del demonio.
3.  **`bootstrap.yml`**: Gestión del estado de inicialización y desbloqueo (Unseal).
4.  **`provision.yml`**: Punto de control para la configuración lógica.

### **📁 `tasks/provisioning/` (Gestión de API)**
Implementa el uso de `vault_write` para suplir la falta de módulos administrativos nativos:
* **`auth/approle.yml`**: Habilitación de métodos de autenticación (AppRole).
* **`policies/main.yml`**: Registro de políticas ACL.
* **`roles/ci_runner.yml`**: Creación de identidades y generación de secretos.
* **`engines/`**: Configuración de secretos dinámicos para PostgreSQL y Redis.

[Image of HashiCorp Vault infrastructure showing the relationship between core server, storage, and API access]

---

## **3. Escenarios de Molecule (Laboratorio de Pruebas)**

### **Escenario `default`**
* **`molecule.yml`**: Configura el driver Docker y el inventario de pruebas.
* **`prepare.yml`**: Tarea crítica que instala `python3-pip` y `hvac` en el contenedor para habilitar los módulos `community.hashi_vault`.
* **`tests/`**: Implementación de pruebas BDD (Gherkin) para validar que el servidor está "Healthy". Incluye archivos `.feature` para definir el comportamiento esperado.

### **Escenario `integration-postgres`**
* Escenario avanzado diseñado para validar la conectividad de Vault con bases de datos externas y la generación de secretos dinámicos específicos para PostgreSQL.

---

## **4. Glosario de Variables Clave**

Estas variables se encuentran en `defaults/main.yml



---



## **Guía de lectura del diagrama**

Para interpretar correctamente la arquitectura representada, ten en cuenta las siguientes convenciones:

* **Jerarquía de Carpetas**: Los bloques anidados representan la estructura física de directorios tal como debe residir en tu espacio de trabajo de VS Code.
* **Código de Colores**:
    * **Rosa / Amarillo**: Identifican archivos de configuración y código fuente del rol de Ansible.
    * **Verde**: Representa el punto de entrada de la pipeline de pruebas (**Molecule**).
    * **Azul (Flechas)**: Indica el flujo de orquestación de la infraestructura (creación y preparación del contenedor).
    * **Naranja (Flechas)**: Define el ciclo de vida interno de la instalación y configuración del sistema operativo.
    * **Verde Oscuro (Flechas)**: Describe el flujo de configuración lógica mediante la API de Vault.
    * **Rojo (Flechas punteadas)**: Señala la generación de artefactos y archivos de salida (secretos y llaves).

---

## **Propósitos de las piezas clave**

Cada componente cumple una función crítica en la automatización del servidor:

* **`molecule/`**: Actúa exclusivamente como el **entorno de laboratorio**. Este directorio no se despliega en producción; su única finalidad es validar y testear que el rol cumple con los requisitos antes del despliegue real.
* **`tasks/bootstrap.yml`**: Es el componente más crítico del rol. Se encarga de la lógica de **inicialización y apertura (Unseal)**. Sin esta pieza, Vault permanecería bloqueado y cualquier intento de interactuar con la API resultaría en un error.
* **`provisioning/`**: Contiene la **lógica de negocio**. Es el lugar donde se definen los parámetros de seguridad, la jerarquía de usuarios y los niveles de permisos (ACL) que regirán tu infraestructura de secretos.

---



## 1. Diagrama de Secuencia UML (Proceso Completo)Este diagrama representa el ciclo de vida de la ejecución desde que lanzas molecule converge hasta la persistencia de las credenciales finales.### Descripción del Flujo y ObjetosOrquestación: Molecule actúa como el director de orquesta, gestionando el ciclo de vida del contenedor Docker.Preparación: Se inyecta la librería hvac en el contenedor, objeto crítico para que Ansible "hable" con la API de Vault.Bootstrapping: Es el paso más sensible. Vault entrega las llaves de cifrado en texto plano (JSON) y Ansible las protege moviéndolas inmediatamente al host local (Mac).Aprovisionamiento Modular: Se utiliza el endpoint sys/ de la API para configurar la seguridad (Auth y Policies) y el endpoint auth/approle para generar identidades dinámicas.## 2. Ficheros del Proyecto y ResponsabilidadesComponenteArchivo de Tarea (.yml)Objeto / Dato ClaveResultadoInstalacióntasks/install.ymlBinario vaultDirectorios /etc/vault.d y /opt/vault/data creados.Serviciotasks/service.ymlUnidad systemdProceso vault server activo en el puerto 8200.Bootstraptasks/bootstrap.ymlvault_init_output.jsonVault en estado Unsealed y Root Token disponible.Auth Methodauth/approle.ymlsys/auth/approleMétodo AppRole habilitado (Idempotente).Policiespolicies/main.ymlci-runner-policy.hclACLs cargadas en el motor de políticas de Vault.App Rolesroles/ci_runner.ymlrole_id & secret_idCredenciales finales guardadas en archivos .txt en el Mac.## 3. Guía de Ejecución (README.md)Copia este bloque en un archivo llamado README.md en la raíz de tu repositorio para finalizar la documentación:Markdown# Laboratorio IaC: Automatización de HashiCorp Vault con Molecule

Este proyecto automatiza el despliegue y aprovisionamiento de un servidor HashiCorp Vault utilizando Ansible y Molecule para pruebas unitarias en entornos aislados de Docker.

## Requisitos Previos
- Docker Desktop (con socket habilitado).
- Python 3.11+ y Virtualenv.
- Colecciones de Ansible: `community.hashi_vault`, `community.docker`, `ansible.posix`.

## Estructura de Aprovisionamiento
El aprovisionamiento se divide en fases modulares:
1. **Fase 1-2**: Instalación del binario y gestión del servicio Systemd.
2. **Fase 3**: Inicialización y Unseal automático (Persistencia de llaves en `/files`).
3. **Fase 4**: Configuración de seguridad (AppRole, Políticas ACL) y generación de identidades.

## Comandos Rápidos
```bash
# Instalar dependencias
ansible-galaxy collection install -r requirements.yml -p ./collections

# Ejecutar el laboratorio completo
export ANSIBLE_COLLECTIONS_PATH=$(pwd)/collections
molecule converge

# Limpiar el entorno
molecule destroy
Seguridad de CredencialesTras una ejecución exitosa, los siguientes artefactos se generan en roles/vault_server/files/:vault_init_output.json: Llaves maestras y Root Token.ci_runner_role_id.txt: ID de rol para el Runner de CI.ci_runner_secret_id.txt: Secreto de acceso para el Runner de CI.