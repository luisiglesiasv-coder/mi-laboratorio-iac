# # 🛠️ Infrastructure-as-Code (IaC) Laboratory Reference

**Project:** PostgreSQL Ansible Role with Molecule Testing  
**Environment:** macOS Ventura (13.7) | MacBook Pro 2017 (Intel)  
**Date:** December 2025  

---

## ## 1. System Level & Virtualization Layer
**Goal:** Establish a stable foundation for running Linux containers on legacy macOS.

* **Compiler Fix:** Resolved `clang` issues to allow Homebrew and Python to compile native extensions.
    * Command: `xcode-select --install`
* **Virtualization Backend:** Installed **QEMU** to provide the backend for the container runtime.
    * Command: `brew install qemu`
* **Docker Engine:** Installed **Docker Desktop v4.48.0** (last stable for macOS 13).
    * **Critical Setting:** "Allow the default Docker socket to be used" must be **Enabled** in *Settings -> Advanced*.



---

## ## 2. Docker Socket & Keychain Configuration
**Goal:** Ensure seamless communication between the Python SDK and the Docker Engine.

* **Socket Pathing:** Created a persistent symbolic link so Molecule can find the Docker daemon.
    ```bash
    sudo ln -sf /Users/luis/.docker/run/docker.sock /var/run/docker.sock
    ```
* **Keychain Fix:** Prevented terminal hangs during builds by disabling the macOS credential store.
    * **File:** `~/.docker/config.json`
    * **Action:** Remove the line `"credsStore": "desktop"` or change it to `"credsStore": ""`.

---

## ## 3. Python Development Environment
**Goal:** Resolve "Unsupported URL scheme" errors and library version conflicts.

A dedicated **Virtual Environment (venv)** is required with **strictly pinned versions** to match legacy OS constraints:

```bash
# Creation and activation
python3 -m venv venv
source venv/bin/activate

# Mandatory version pinning
pip install "urllib3<2" "requests==2.31.0" "docker==6.1.3"
pip install "molecule-plugins[docker]"
```
---

---

## ## 4. Molecule Scenario Architecture
**Goal:** Configure a container that behaves like a real systemd-managed server.

### ### molecule/default/molecule.yml
```yaml
driver:
  name: docker
platforms:
  - name: instance
    image: geerlingguy/docker-ubuntu2204-ansible:latest
    privileged: true
    command: /sbin/init  # Vital for systemd support
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host
provisioner:
  name: ansible
```

---

## ## 5. PostgreSQL Role & Testing Logic
**Goal:** Automate database setup and verify it via SQL.

### ### molecule/default/verify.yml
```yaml
- name: Verify PostgreSQL Data Plane
  hosts: all
  tasks:
    - name: Run SQL query as postgres user
      community.postgresql.postgresql_query:
        db: "app_db"
        login_user: "postgres"
        query: "SELECT current_database();"
      register: db_name_output
      become: true           # Required for Peer Auth
      become_user: postgres  # Switches to the DB owner account

    - name: Assert Database Existence
      ansible.builtin.assert:
        that: "db_name_output.query_result[0].current_database == 'app_db'"
        success_msg: "SQL verified: app_db is active and reachable."
```

---

## ## 6. The DevOps Workflow Cheat Sheet

| **Command** | **Action** |
| :--- | :--- |
| `molecule create` | Provisions the Ubuntu container. |
| `molecule converge` | Applies the Ansible role (Installation & Configuration). |
| `molecule verify` | Executes the SQL tests defined in `verify.yml`. |
| `molecule login` | Opens an interactive shell inside the container. |
| `molecule destroy` | Tears down the environment and frees system resources. |

---

## ## 7. Key Engineering Learnings
1.  **Idempotency:** A successful `molecule converge` followed by another should result in **`changed=0`**. This ensures the code is safe for production.
2.  **Privilege Escalation:** `become: true` is essential when interacting with system services that rely on local user verification.
3.  **Dependency Pinning:** In legacy environments, stability is achieved by matching library versions to the OS, rather than using the "latest" available.
   
---
---

## ## 8. Automation Script: Environment Initializer
**Goal:** Provide a one-click solution to recreate the entire laboratory environment, including dependency pinning and macOS path fixes.

### ### init_lab.sh
```bash
#!/bin/bash

# ==============================================================================
# INFRASTRUCTURE LAB INITIALIZATION SCRIPT
# Purpose: Sets up Python venv, pins dependencies, and fixes macOS Docker paths.
# Compatibility: macOS Ventura (13.7) | Intel MacBook Pro
# ==============================================================================

set -e  # Exit immediately if a command exits with a non-zero status.

echo "🚀 Starting Infrastructure Lab Setup..."

# 1. Clean up old environment if exists
if [ -d "venv" ]; then
    echo "🧹 Removing old virtual environment..."
    rm -rf venv
fi

# 2. Create and activate Virtual Environment
echo "📦 Creating Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate

# 3. Install and Pin Dependencies
# Specific versions for compatibility with macOS Ventura and Docker 4.48.0
echo "🛠️  Installing pinned dependencies (Ansible, Molecule, Docker SDK)..."
pip install --upgrade pip
pip install "urllib3<2" "requests==2.31.0" "docker==6.1.3"
pip install "ansible-core>=2.15.0"
pip install "molecule-plugins[docker]"

# 4. macOS Docker Socket Fix
echo "🔗 Linking Docker socket to standard path..."
if [ -S "/Users/$USER/.docker/run/docker.sock" ]; then
    sudo ln -sf "/Users/$USER/.docker/run/docker.sock" /var/run/docker.sock
    echo "✅ Socket linked successfully."
else
    echo "⚠️  Warning: Docker Desktop socket not found at expected user path."
fi

# 5. Fix Credential Store Error
if [ -f "$HOME/.docker/config.json" ]; then
    echo "🔐 Patching Docker config.json to bypass Keychain issues..."
    sed -i '' 's/"credsStore":[[:space:]]*"desktop"/"credsStore": ""/g' "$HOME/.docker/config.json"
fi

echo "----------------------------------------------------"
echo "✅ SETUP COMPLETE!"
echo "----------------------------------------------------"
echo "To start working, run:"
echo "  source venv/bin/activate"
echo "  molecule list"
echo "----------------------------------------------------"
```

### ### Implementation Steps
1. **Create the file**: Save the code into `init_lab.sh` in the project root.
2. **Grant execution permissions**:
   ```bash
   chmod +x init_lab.sh
   ```
3. **Run the script**:
   ```bash
   ./init_lab.sh
   ```

### ### Why this is necessary
* **Reliability**: Ensures that every time you work on the project, you are using the exact same library versions that were proven to work.
* **Socket Persistence**: macOS often loses symbolic links in `/var/run` after a reboot; this script restores them instantly.
* **Environment Isolation**: Prevents global Python updates on your Mac from breaking your Molecule testing suite.

---

## ## 9. Role Logic: PostgreSQL Implementation
**Goal:** Define the actual work performed by Ansible within the containerized environment.

### ### tasks/main.yml
```yaml
---
# Main tasks for the postgres_server role

- name: Install PostgreSQL and required Python libraries
  # Required packages for the engine and for Ansible's postgresql modules
  ansible.builtin.apt:
    name:
      - postgresql
      - postgresql-contrib
      - python3-psycopg2
    state: present
    update_cache: yes

- name: Ensure PostgreSQL is started and enabled
  # Managing the service via systemd inside the container
  ansible.builtin.service:
    name: postgresql
    state: started
    enabled: yes

- name: Create PostgreSQL database
  # Provisioning the target application database
  community.postgresql.postgresql_db:
    name: "{{ postgres_db_name }}"
    login_user: postgres
  become: true
  become_user: postgres

- name: Create PostgreSQL user
  # Provisioning the user with specific privileges
  # Note: 'priv' is used due to current collection version constraints
  community.postgresql.postgresql_user:
    db: "{{ postgres_db_name }}"
    name: "{{ postgres_user_name }}"
    password: "{{ postgres_user_password }}"
    priv: "ALL"
    login_user: postgres
  become: true
  become_user: postgres
```

### ### handlers/main.yml
```yaml
---
# Handlers to respond to configuration changes

- name: Restart PostgreSQL
  ansible.builtin.service:
    name: postgresql
    state: restarted
```

---

## ## 10. Role Variables (defaults/main.yml)
**Goal:** Centralize configuration to allow easy changes without modifying tasks.

```yaml
---
postgres_db_name: "app_db"
postgres_user_name: "app_user"
postgres_user_password: "secure_password_123"
```

---

## ## 11. Molecule Core Configuration Files
**Goal:** Define the environment lifecycle and the provisioner strategy.

### ### molecule/default/molecule.yml
**Purpose:** This is the "Master Blueprint." it defines which driver to use (Docker), how the infrastructure should look (Ubuntu), and what tools will manage the lifecycle.

```yaml
---
driver:
  name: docker  # Specifies the engine that creates the test environment
platforms:
  - name: instance  # The inventory name of the test node
    image: geerlingguy/docker-ubuntu2204-ansible:latest  # Systemd-enabled base image
    privileged: true  # Necessary for systemd to manage services like PostgreSQL
    command: /sbin/init  # Starts the init process required by systemd
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw  # Maps control groups for service management
    cgroupns_mode: host  # Critical for cgroup compatibility on macOS hosts
provisioner:
  name: ansible  # Uses Ansible to apply roles and verify the state
verifier:
  name: ansible  # Uses Ansible playbooks for the verification phase
```



---

### ### molecule/default/converge.yml
**Purpose:** This is the "Test Entrypoint." It is a standard Ansible Playbook that Molecule runs to apply your role to the freshly created infrastructure.

```yaml
---
- name: Converge
  hosts: all  # Targets all instances defined in the platforms section
  gather_facts: true  # Collects OS info (distro, version) needed for apt tasks
  tasks:
    - name: "Include postgres_server"
      # This dynamically loads your role into the Molecule execution
      include_role:
        name: "postgres_server"
```

---

## ## 12. Deep Dive: Why these settings matter?

### ### The `privileged: true` & `/sbin/init` Combo
In a standard Docker container, you cannot run `systemctl start postgresql`. Why? Because containers are just processes, not full OS instances.
* **The Fix**: By setting the container to **privileged** and running **init**, we trick the container into thinking it is a real server. This is the only way to test "Service" modules in Ansible accurately.

### ### The `volumes` & `cgroupns_mode` Fix
On **macOS Intel (Ventura)**, the way Docker handles Control Groups (cgroups) is different from native Linux.
* **The Fix**: Mapping `/sys/fs/cgroup` and setting the namespace mode to **host** prevents the "Failed to connect to bus" error that usually happens when Ansible tries to talk to systemd.

### ### The `include_role` strategy
We use `include_role` instead of a simple task list. This ensures that:
1.  **Handlers** are correctly triggered (e.g., restarting Postgres after a config change).
2.  **Default variables** are loaded with the correct precedence.
3.  **Molecule** tests the role exactly as it would be used in a production Playbook.


---

## ## 13. Execution Lifecycle & Output Analysis
**Goal:** Connect terminal actions with the configuration files to understand the underlying automation logic.

### ### 13.1 Step 1: `molecule create`
**Purpose:** Provisions the virtual hardware (containers) defined in `molecule.yml`.

**Terminal Execution:**
```bash
(venv) luis@Luiss-MacBook-Pro postgres_server % molecule create  
INFO     default ➜ create: Executing
PLAY [Create] ******************************************************************
TASK [Create molecule instance(s)] *********************************************
changed: [localhost] => (item=instance)
PLAY RECAP *********************************************************************
localhost                  : ok=9    changed=4 ...
INFO     default ➜ create: Executed: Successful
```

**Architecture Link:**
* **`molecule.yml`**: Molecule reads the `platforms` section, pulls the Ubuntu image, and starts a container named `instance`.
* **Validation**: Running `docker ps` after this command shows the container running with `/sbin/init`, confirming that the `command` override in our YAML is active.

---

### ### 13.2 Step 2: `molecule converge` (Initial Run)
**Purpose:** Executes the primary Ansible role logic on the blank container.

**Terminal Execution:**
```bash
(venv) luis@Luiss-MacBook-Pro postgres_server % molecule converge
PLAY [Converge] ****************************************************************
TASK [postgres_server : Install PostgreSQL...] ****** changed: [instance]
TASK [postgres_server : Ensure PostgreSQL is started...] ****** changed: [instance]
TASK [postgres_server : Create PostgreSQL database] ****** changed: [instance]
TASK [postgres_server : Create PostgreSQL user] ****** changed: [instance]
PLAY RECAP *********************************************************************
instance                   : ok=5    changed=4 ...
```

**Architecture Link:**
* **`converge.yml`**: This file acts as the bridge, telling Molecule to include your role.
* **`tasks/main.yml`**: Every task shows `changed` because the container was in a "clean" state. Ansible is actively modifying the OS to match your code.

---

### ### 13.3 Step 3: `molecule converge` (Idempotency Test)
**Purpose:** Ensures the role is safe to re-run and won't make unnecessary changes.

**Terminal Execution:**
```bash
(venv) luis@Luiss-MacBook-Pro postgres_server % molecule converge
...
TASK [postgres_server : Install PostgreSQL...] ****** ok: [instance]
...
PLAY RECAP *********************************************************************
instance                   : ok=5    changed=0 ...
```

**Architecture Link:**
* **Logic Check**: Ansible detects that PostgreSQL is already installed and the database exists. Since the current state matches the desired state, it reports `changed=0`. This is the "Gold Standard" for infrastructure stability.

---

### ### 13.4 Step 4: `molecule verify`
**Purpose:** Runs automated functional tests against the live service.

**Terminal Execution:**
```bash
(venv) luis@Luiss-MacBook-Pro postgres_server % molecule verify  
PLAY [Verify] ******************************************************************
TASK [Check if PostgreSQL is listening on port 5432] ***************************
ok: [instance]
TASK [Execute a basic SQL query to confirm database presence] ******************
ok: [instance]
TASK [Assert connectivity to the target database] ******************************
ok: [instance] => { "msg": "Success! SQL connection verified for database app_db." }
```

**Architecture Link:**
* **`verify.yml`**: This file executes queries against the engine. It proves that the "Data Plane" (PostgreSQL) is not just running, but actually accepting SQL commands.

---

### ### 13.5 Step 5: `molecule destroy`
**Purpose:** Reclaims system resources by removing the test environment.

**Terminal Execution:**
```bash
(venv) luis@Luiss-MacBook-Pro postgres_server % molecule destroy
TASK [Destroy molecule instance(s)] ********************************************
changed: [localhost] => (item=instance)
(venv) luis@Luiss-MacBook-Pro postgres_server % docker ps
# Returns empty list
```

**Architecture Link:**
* **Lifecycle Completion**: Molecule instructs Docker to kill and delete the `instance`. This returns your Mac's CPU and RAM to a baseline state.

---

## ## 14. Summary: File-to-Command Mapping

| **File** | **Responsibility** | **Trigger Command** |
| :--- | :--- | :--- |
| **`molecule.yml`** | Defines the "Virtual Hardware" | `molecule create` |
| **`tasks/main.yml`** | Defines the "Installation Logic" | `molecule converge` |
| **`converge.yml`** | Connects the role to Molecule | `molecule converge` |
| **`verify.yml`** | Defines "Health Checks" | `molecule verify` |


## ## 🏁 Final Conclusion
You have built a **fully automated, test-driven local infrastructure laboratory**. By combining Docker, Molecule, and Ansible, you can now develop complex infrastructure roles on your macOS Ventura system with the same level of confidence as in a production CI/CD environment.

**Workflow Reminder:**
1. Edit `tasks/main.yml`
2. Run `molecule converge`
3. Run `molecule verify`
4. If satisfied, run `molecule destroy`