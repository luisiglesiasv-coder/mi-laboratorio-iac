# Role: Nexus

Deploys and configures a self-hosted Sonatype Nexus Repository Manager 3 instance using Docker. This role handles the full stack setup, from installing the Docker engine to configuring NFS persistent storage and exposing specific ports for container registry usage.

## 📋 Requirements

- **Target OS**: Ubuntu (Tested on 24.04/25.10).
- **Storage**: An external NFS Server (NAS) reachable from the host.
- **Network**: Static IP recommended for the host.

## 🔧 Role Variables

These variables are critical for the correct mounting of persistence data and container deployment. They should be defined in `group_vars/all.yml` or the inventory.

| Variable | Description | Example |
|----------|-------------|---------|
| `nexus_nas_ip` | IP address of the NFS/NAS server | `"10.0.0.100"` |
| `nexus_nas_path` | Remote path exported by the NFS server | `"/volume1/nexus_data"` |
| `nexus_mount_point` | Local directory where data will be mounted | `"/mnt/nexus_data"` |
| `nexus_nas_uid` | User ID on the host to match NAS file permissions | `"1026"` |
| `nexus_nas_user` | Cosmetic username for the NFS user | `"nexus_user"` |
| `nexus_image` | Docker image and tag to deploy | `"sonatype/nexus3:3.70.1"` |
| `nexus_container_name` | Name of the Docker container | `"nexus-server"` |
| `nexus_memory_limit` | RAM limit for the Java container | `"3g"` |

## ⚙️ Functionality

1. **Docker Preparation**:
   - Installs Docker Engine (if missing).
   - Installs the Python Docker SDK (`python3-docker`) required by Ansible.

2. **Persistence Layer (NFS)**:
   - Installs `nfs-common`.
   - Creates a local dummy user to map UID/GID with the NAS.
   - Mounts the NFS share with optimized options (`rw,hard,noatime`) for stability.

3. **Container Deployment**:
   - Stops and removes any previous container to ensure configuration updates.
   - Deploys Nexus with **Restart Policy: Always**.
   - **Exposed Ports**:
     - `8081`: Web UI, Maven, PyPI, Nuget.
     - `8082`: Dedicated Docker Registry Connector (HTTP).

## 🚀 Example Usage

```yaml
- hosts: nexusservers
  become: true
  roles:
    - nexus
```

## ARchitecture Diagram

```
@startuml
' Configuración de estilos manual
skinparam componentStyle uml2
skinparam shadowing false
skinparam handwritten false
skinparam roundcorner 5
skinparam backgroundColor white

' Definición de colores
skinparam node {
    BackgroundColor White
    BorderColor #0077BE
    FontColor Black
}
skinparam component {
    BackgroundColor #E1F5FE
    BorderColor #0277BD
    FontColor Black
}
skinparam interface {
    BackgroundColor Black
    BorderColor Black
}
skinparam database {
    BackgroundColor #E1F5FE
    BorderColor #0277BD
}
skinparam note {
    BackgroundColor #FFF9C4
    BorderColor #FBC02D
}

title Nexus Role Architecture

' Actores y Clientes
actor "SysAdmin / Ansible" as Admin
cloud "Lab Clients\n(Runners, DB Nodes)" as Clients

' Infraestructura Externa (NAS)
node "NAS Server (Storage)" as NAS {
    database "NFS Export\n/volume1/nexus_data" as NAS_Data
}

' El Servidor Nexus (Host)
node "Nexus Host (Ubuntu)" as Host {
    
    package "Operating System" {
        folder "Local Mount\n/mnt/nexus_data" as Local_Mount
        interface "NFS Client" as NFS_Client
    }

    ' CAMBIO AQUÍ: Usamos 'rectangle' en lugar de 'rect'
    rectangle "Docker Runtime" {
        component "Sonatype Nexus 3\n(Container)" as NexusContainer {
            port "8081" as P8081_Int
            port "8082" as P8082_Int
            folder "/nexus-data" as Vol_Int
        }
    }
    
    port "Host Port: 8081" as P8081_Ext
    port "Host Port: 8082" as P8082_Ext
}

' Relaciones de Despliegue
Admin ..> Host : SSH (Deploy Role)

' Relaciones de Almacenamiento
NFS_Client --> NAS_Data : NFS Protocol\n(rw,hard,noatime)
Local_Mount -up-> NFS_Client
Vol_Int ..> Local_Mount : Docker Volume\nBind Mount

' Relaciones de Red (Puertos)
P8081_Ext <--> P8081_Int : Map
P8082_Ext <--> P8082_Int : Map

' Flujo de Tráfico
Clients --> P8081_Ext : HTTP (Web UI, PyPI, Maven)
Clients --> P8082_Ext : HTTP (Docker Registry Mirror)

note right of P8082_Ext
  Dedicated Port for
  Docker Connector
end note

@enduml
```