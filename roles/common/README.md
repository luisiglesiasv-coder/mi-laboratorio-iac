# Role: Common

Configures the base infrastructure for lab clients. Its main purpose is to redirect package manager traffic (Docker, Pip) to the local Nexus server to optimize bandwidth usage and enable offline capabilities.

## 📋 Requirements

- An operational Nexus 3 server.
- Docker installed on the target node (or ready to be installed/configured).
- Python 3 installed.

## 🔧 Role Variables

These variables should be defined in `group_vars/all.yml` or your inventory file:

| Variable | Description | Example |
|----------|-------------|---------|
| `nexus_ip` | IP address of the Nexus server | `"10.0.0.127"` |
| `nexus_docker_port` | Port exposed on Nexus for the Docker HTTP connector | `"8082"` |
| `nexus_docker_url` | Full URL for the Docker mirror | `"http://10.0.0.127:8082/"` |
| `nexus_pypi_url` | URL for the PyPI repository (Simple index) | `"http://10.0.0.127:8081/repository/pypi-proxy/simple"` |

## ⚙️ Functionality

1. **Docker**:
   - Configures `/etc/docker/daemon.json`.
   - Adds Nexus as a `registry-mirror` (Transparent Proxy).
   - Adds Nexus as an `insecure-registry` (Allows HTTP traffic on port 8082).
   - Restarts the Docker service automatically if changes are applied.

2. **Python (Pip)**:
   - Configures `/etc/pip.conf` globally.
   - Sets the `index-url` to point to Nexus.
   - Marks the Nexus host as a `trusted-host`.

## 🚀 Example Usage

```yaml
- hosts: all
  become: true
  roles:
    - common