# Enterprise Linux Server Management Suite (Core Engine)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)

A fully asynchronous, high-performance backend core engine for managing enterprise Linux infrastructures. Provides secure REST APIs and WebSocket streams for system metrics, `systemd` service control, **multi-version Oracle DB** administration, **full MS SQL Server** management (T-SQL, backups), **dynamic Prometheus target discovery**, and **Loki log querying**.

## 🚀 Key Features

- 📊 **Real-time Metrics**: Live system snapshots (CPU, RAM, Disk) and persistent WebSocket streaming.
- 🖥️ **Systemd Management**: Start, stop, restart, and stream logs for critical services (Nginx, Docker, PostgreSQL, MS SQL, Oracle XE, etc.).
- 🗄️ **Oracle DB Admin (All Versions)**: Silent creation of single-tenant or multi-tenant (CDB/PDB) Oracle databases via DBCA, and startup/shutdown control via `dbstart`/`dbshut`.
- 🗄️ **MS SQL Server Management (All Versions)**: Execute T-SQL queries, create/drop databases, trigger full backups via `sqlcmd`, and manage service state.
- 📈 **Dynamic Prometheus Targets**: Register or remove new scrape targets via REST API (auto-updates `targets.json` for file-based service discovery).
- 📋 **Loki Log Query Proxy**: Direct API access to Grafana Loki's `query_range` endpoint (LogQL) with JWT authentication.
- 🔒 **Security-First**: JWT-based authentication, bcrypt password hashing, strict CORS, and rate-limiting via Nginx.

## 📋 Prerequisites

- **Linux Host** with `systemd` and `journald` installed (for service control and log streaming).
- **Docker** & **Docker Compose** (v2.0+).
- **Git**.
- **(Optional)** SSL certificates from Let's Encrypt (placed at `/etc/letsencrypt` for HTTPS).
- **Permissions**: The container requires read access to `/proc`, `/sys`, `/var/log/journal`, and `/run/systemd`. Ensure the user running Docker has these permissions or run as root.
- **Directory Setup (Required for Dynamic Prometheus)**:
  ```bash
  mkdir -p ./prometheus_targets
  chmod 755 ./prometheus_targets
