# Enterprise Linux Server Management Suite (Core Engine)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)

An asynchronous, high-performance backend core engine for managing enterprise Linux servers. Provides secure REST APIs and WebSocket streams for system metrics, `systemd` service control, and multi-version Oracle Database instance administration.

## 🚀 Key Features

- 📊 **Real-time Metrics**: Live system snapshots (CPU, RAM, Disk) and persistent WebSocket streaming.
- 🖥️ **Systemd Management**: Start, stop, restart, and stream logs for critical services (Nginx, Docker, PostgreSQL, Oracle XE, etc.).
- 🗄️ **Oracle DB Admin**: Silent creation of single-tenant or multi-tenant (CDB/PDB) Oracle databases via DBCA, and startup/shutdown control.
- 📈 **Observability Stack**: Pre-configured with Prometheus (metrics), Loki (log aggregation), and Grafana (dashboards).
- 🔒 **Security-First**: JWT-based authentication, bcrypt password hashing, and strict CORS policies.

## 📋 Prerequisites

- **Linux Host** with `systemd` and `journald` installed (for service control and log streaming).
- **Docker** & **Docker Compose** (v2.0+).
- **Git**.
- **(Optional)** SSL certificates from Let's Encrypt (placed at `/etc/letsencrypt` for HTTPS).
- **Permissions**: The container requires read access to `/proc`, `/sys`, `/var/log/journal`, and `/run/systemd`. Ensure the user running Docker has these permissions or run as root.

## 🛠️ Environment Variables (.env)

Create a `.env` file in the project root. **Do not commit this file to version control.**

| Variable | Description | Example |
| :--- | :--- | :--- |
| `SECRET_KEY` | **Required**. Crypto-secure random hex string for JWT signing. Generate via `openssl rand -hex 32`. | `9a8b7c6d...` |
| `ALGORITHM` | JWT signing algorithm. Default `HS256`. | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiry time. | `60` |
| `FIRST_SUPERUSER` | **Recommended**. Username for the initial admin account. | `admin` |
| `FIRST_SUPERUSER_PASSWORD` | **Recommended**. Strong password for the initial admin account. | `yourStrongP@ssw0rd` |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend domains. | `https://myfrontend.com,https://app.example.com` |
| `DATABASE_URL` | SQLite connection string. Default uses `./server_manager.db`. | `sqlite+aiosqlite:///./server_manager.db` |

## 🏁 Quick Start (Production Deployment)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/swelehwaseem-pixel/server-manager-backend.git
    cd server-manager-backend
