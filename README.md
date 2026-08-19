# Enterprise Linux Server Management Suite (Core Engine)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?logo=ubuntu&logoColor=white)](https://ubuntu.com)
[![RHEL](https://img.shields.io/badge/RHEL-EE0000?logo=redhat&logoColor=white)](https://redhat.com)

A fully asynchronous, high-performance backend core engine for managing enterprise Linux infrastructures. Provides secure REST APIs and WebSocket streams for system metrics, `systemd` service control, **multi-version Oracle DB** administration, **full MS SQL Server** management (T-SQL, backups, user management), **dynamic Prometheus target discovery**, and **Loki log querying**.

## 🚀 Key Features

- 📊 **Real-time Metrics**: Live system snapshots (CPU, RAM, Disk) and persistent WebSocket streaming.
- 🖥️ **Systemd Management**: Start, stop, restart, and stream logs for critical services (Nginx, Docker, PostgreSQL, MS SQL, Oracle XE, etc.).
- 🗄️ **Oracle DB Admin (All Versions)**:
  - Execute SQL queries (Thin Mode - NO Oracle Client required)
  - Silent creation of single-tenant or multi-tenant (CDB/PDB) databases via DBCA
  - Startup/shutdown control via `dbstart`/`dbshut`
  - RMAN Full & Incremental backups
  - RMAN Restore with recovery
  - EXPDP Data Pump exports
  - IMPDP Data Pump imports
- 🗄️ **MS SQL Server Management (All Versions)**:
  - Execute T-SQL queries
  - Create / Drop databases
  - Full database backups & restores (using `sqlcmd`)
  - Create / Drop database users with role assignment
- 📈 **Dynamic Prometheus Targets**: Register or remove new scrape targets via REST API (auto-updates `targets.json` for file-based service discovery).
- 📋 **Loki Log Query Proxy**: Direct API access to Grafana Loki's `query_range` endpoint (LogQL) with JWT authentication.
- 🐧 **Linux Script Executor**: Securely execute bash scripts via REST API with built-in safety blocks (prevents `rm -rf /`, `forkbombs`, etc.).
- 🔒 **Security-First**: JWT-based authentication, bcrypt password hashing, strict CORS, and rate-limiting via Nginx.

## 📋 Prerequisites (Host OS Requirements)

Before running the application, ensure your **fresh Linux host** has the following installed and configured. These steps are **required before** running `docker compose`.

### 1. Core Infrastructure
| Component | Why It's Needed | Installation Command (Ubuntu/Debian) | Installation Command (RHEL/UBI) |
| :--- | :--- | :--- | :--- |
| **Docker Engine** | To run the containers. | `sudo apt update && sudo apt install -y docker.io docker-compose` | `sudo dnf install -y docker-ce docker-compose` |
| **Git** | To clone the repository. | `sudo apt install -y git` | `sudo dnf install -y git` |
| **Docker User Permissions** | Allow Docker to read host system files. | `sudo usermod -aG docker $USER && newgrp docker` | `sudo usermod -aG docker $USER && newgrp docker` |

### 2. Oracle Database Management (Required for Oracle Features)
| Component | Why It's Needed | Setup Instructions |
| :--- | :--- | :--- |
| **Oracle Binaries & User** | The backend executes `dbstart`, `dbshut`, `rman`, `expdp`, `impdp`, and `dbca` on the host via `sudo -u oracle`. | Install Oracle 11g/12c/18c/19c/21c/23ai with a user named `oracle`. |
| **Sudoers Rule (Host)** | Allows the container's `root` user to execute Oracle binaries as the `oracle` user **without a password**. | Create `/etc/sudoers.d/oracle` with: <br> `root ALL=(oracle) NOPASSWD: /u01/app/oracle/product/*/bin/dbstart, /u01/app/oracle/product/*/bin/dbshut, /u01/app/oracle/product/*/bin/rman, /u01/app/oracle/product/*/bin/expdp, /u01/app/oracle/product/*/bin/impdp, /u01/app/oracle/product/*/bin/dbca` |

### 3. Shared Volumes & Directories
| Component | Why It's Needed | Setup Command |
| :--- | :--- | :--- |
| **Prometheus Targets Directory** | Shared volume for dynamic Prometheus target discovery. | `mkdir -p ./prometheus_targets && chmod 755 ./prometheus_targets` |
| **SSL Certificates (Optional)** | For HTTPS via Nginx. | `sudo mkdir -p /etc/letsencrypt/live/yourdomain.com` (Place `fullchain.pem` and `privkey.pem` inside) |
| **Backup Directories (Optional)** | For RMAN/EXPDP and MSSQL backups. | `sudo mkdir -p /backup/oracle /backup/mssql` |

### 4. System Services (Pre-installed on Fresh Linux)
- ✅ **`systemd`** – Required for service control (`/api/v1/services`).
- ✅ **`journald`** – Required for log streaming (`/api/v1/services/stream/{name}`).

## 🛠️ Environment Variables (.env)

Create a `.env` file in the project root. **Do not commit this file to version control.**

| Variable | Description | Example |
| :--- | :--- | :--- |
| `SECRET_KEY` | **Required**. Crypto-secure random hex string for JWT signing. Generate via `openssl rand -hex 32`. | `9a8b7c6d...` |
| `ALGORITHM` | JWT signing algorithm. Default `HS256`. | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiry time. | `60` |
| `FIRST_SUPERUSER` | **Recommended**. Username for the initial admin account. | `admin` |
| `FIRST_SUPERUSER_PASSWORD` | **Recommended**. Strong password for the initial admin account. | `yourStrongP@ssw0rd` |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend domains. | `https://myfrontend.com,http://localhost:3000` |
| `DATABASE_URL` | SQLite connection string. Default uses `./server_manager.db`. | `sqlite+aiosqlite:///./server_manager.db` |
| `GRAFANA_PASSWORD` | Admin password for the Grafana UI. | `your_secure_grafana_password` |

## 🏁 Quick Start (Production Deployment)

Follow these steps on a **fresh Linux OS**:

```bash
# 1. Install Docker & Git (Ubuntu example)
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo usermod -aG docker $USER
newgrp docker

# 2. Clone the repository
git clone https://github.com/swelehwaseem-pixel/server-manager-backend.git
cd server-manager-backend

# 3. Create the Prometheus dynamic targets directory (Required!)
mkdir -p ./prometheus_targets
chmod 755 ./prometheus_targets

# 4. (Optional) Create backup directories if you plan to use RMAN/EXPDP or MSSQL backups
sudo mkdir -p /backup/oracle /backup/mssql

# 5. Configure Environment Variables
echo "SECRET_KEY=$(openssl rand -hex 32)" > .env
echo "FIRST_SUPERUSER=admin" >> .env
echo "FIRST_SUPERUSER_PASSWORD=$(openssl rand -hex 12)" >> .env
echo "CORS_ORIGINS=http://localhost:3000,https://your-frontend.com" >> .env
echo "GRAFANA_PASSWORD=your_secure_grafana_password" >> .env

# 6. (Only for Oracle features) Configure sudoers on the HOST
sudo visudo -f /etc/sudoers.d/oracle
# Add the following line:
# root ALL=(oracle) NOPASSWD: /u01/app/oracle/product/*/bin/dbstart, /u01/app/oracle/product/*/bin/dbshut, /u01/app/oracle/product/*/bin/rman, /u01/app/oracle/product/*/bin/expdp, /u01/app/oracle/product/*/bin/impdp, /u01/app/oracle/product/*/bin/dbca

# 7. Build and Launch the Stack (Choose one):

# ✅ For Ubuntu / Debian (Default - uses Dockerfile.ubuntu)
docker compose -f docker-compose.ubuntu.yml up --build -d

# ✅ For RHEL / UBI / Fedora (uses Dockerfile.rhel)
docker compose -f docker-compose.rhel.yml up --build -d

# 8. Verify all services are healthy
docker ps
curl http://localhost:8000/health
