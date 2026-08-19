# Enterprise Linux Server Management Suite (Core Engine)

Asynchronous FastAPI backend proxy for managing metrics, systemd units, logs via Grafana Loki, and multi-version Oracle DB instances.

## 🚀 Deployment Instructions
1. Install Git and Docker on a clean machine.
2. Put your active SSL certificate targets under `/etc/letsencrypt`.
3. Generate your cryptographic signature: `openssl rand -hex 32`
4. Update `docker-compose.yml` with your generated hex string and your domain names.
5. Launch the entire integrated stack:
```bash
docker compose up --build -d
```
*   **API Management Panels:** `https://yourdomain.com`
*   **Grafana Dashboards Analytics:** `http://localhost:3000`
