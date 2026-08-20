from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import generate_latest, Gauge, REGISTRY
import psutil

from app.config import settings
from app.database import engine, Base, get_async_db, User, AsyncSessionLocal
from app.auth import SecurityUtils
from app.schemas.auth import TokenResponse

# 🔥 Import ALL routers (Complete Suite)
from app.routers import (
    metrics,
    services,
    oracle_admin,
    prometheus_targets,
    mssql_admin,
    logs,
    linux_scripts,
    terminal,
    file_browser,
)

# ------------------------------------------------------------------
# Prometheus Gauges (System Metrics)
# ------------------------------------------------------------------
CPU_USAGE = Gauge('server_cpu_usage_percent', 'Current CPU usage in percent', registry=REGISTRY)
RAM_USAGE = Gauge('server_ram_usage_percent', 'Current RAM usage in percent', registry=REGISTRY)
DISK_USAGE = Gauge('server_disk_usage_percent', 'Current Disk usage in percent', registry=REGISTRY)


# ------------------------------------------------------------------
# Lifespan: Database creation + Secure Admin Bootstrapping
# ------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Create initial superuser ONLY if env vars are provided (no hardcoded defaults!)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            if settings.first_superuser and settings.first_superuser_password:
                result = await session.execute(
                    select(User).filter(User.username == settings.first_superuser)
                )
                if not result.scalars().first():
                    admin_user = User(
                        username=settings.first_superuser,
                        hashed_password=SecurityUtils.hash_password(
                            settings.first_superuser_password
                        )
                    )
                    session.add(admin_user)
                    print(f"✅ Superuser '{settings.first_superuser}' created successfully.")
            else:
                print("⚠️  No FIRST_SUPERUSER env vars set. Skipping admin creation.")

    yield

    # 3. Cleanup on shutdown
    await engine.dispose()


# ------------------------------------------------------------------
# FastAPI Application
# ------------------------------------------------------------------
app = FastAPI(
    title="Enterprise Linux Core Engine",
    version="1.0.0",
    lifespan=lifespan,
    description="""
    ## Enterprise Linux Server Management Suite
    
    This API provides comprehensive management capabilities for enterprise Linux servers:
    
    - **System Metrics**: Real-time CPU, RAM, Disk monitoring
    - **Systemd Services**: Start, stop, restart, and stream logs
    - **Oracle Database**: Execute queries, start/stop, create CDB/PDB, RMAN, EXPDP, IMPDP
    - **MS SQL Server**: Execute queries, create/drop databases, backup/restore, user management
    - **Dynamic Prometheus Targets**: Register and manage scrape targets
    - **Log Query (Loki)**: Query aggregated logs using LogQL
    - **Linux Shell**: Interactive terminal (WebSocket) and script execution
    - **File Browser**: List, upload, download, delete, rename, edit files
    """
)

# ------------------------------------------------------------------
# CORS Middleware (Strict, reads from .env)
# ------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ------------------------------------------------------------------
# Global Exception Handler (Prevents stack trace leaks)
# ------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_class": "InternalExecutionError",
            "message": "System trace variation intercepted."
        }
    )


# ------------------------------------------------------------------
# 🩺 Healthcheck Endpoint (For Docker/Kubernetes)
# ------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """
    Liveness probe for container orchestration.
    Returns 200 OK as long as the FastAPI app is running.
    """
    return {"status": "healthy", "service": "server-manager-backend"}


# ------------------------------------------------------------------
# Prometheus Metrics Endpoint
# ------------------------------------------------------------------
@app.get("/metrics", response_class=PlainTextResponse, tags=["Observability"])
async def get_prometheus_metrics():
    """
    Prometheus metrics endpoint.
    Scraped by Prometheus for monitoring CPU, RAM, and Disk usage.
    """
    CPU_USAGE.set(psutil.cpu_percent(interval=None))
    RAM_USAGE.set(psutil.virtual_memory().percent)
    DISK_USAGE.set(psutil.disk_usage("/").percent)
    return PlainTextResponse(content=generate_latest(REGISTRY).decode("utf-8"))


# ------------------------------------------------------------------
# Authentication: Login (JWT Token Generation)
# ------------------------------------------------------------------
@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["Access Rules"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Authenticate and receive a JWT access token.
    
    - Use OAuth2 password flow
    - Returns Bearer token for subsequent API calls
    - Token expires based on ACCESS_TOKEN_EXPIRE_MINUTES setting
    """
    result = await db.execute(select(User).filter(User.username == form_data.username))
    user = result.scalars().first()

    if not user or not SecurityUtils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid system account credentials."
        )

    access_token = SecurityUtils.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# ------------------------------------------------------------------
# Include ALL Routers (Complete Enterprise Suite)
# ------------------------------------------------------------------

# 1. System & Infrastructure
app.include_router(metrics.router)                    # /api/v1/metrics

# 2. Systemd Service Management
app.include_router(services.router)                   # /api/v1/services

# 3. Oracle Database Management
app.include_router(oracle_admin.router)               # /api/v1/oracle
#   - Execute SQL queries (Thin Mode - NO Oracle Client required)
#   - Start/Stop database instances
#   - Create CDB/PDB via DBCA
#   - RMAN Full/Incremental backups & restore
#   - EXPDP Data Pump exports
#   - IMPDP Data Pump imports

# 4. MS SQL Server Management
app.include_router(mssql_admin.router)                # /api/v1/mssql
#   - Execute T-SQL queries
#   - Create/Drop databases
#   - Full database backups & restores
#   - Create/Drop users with role assignment

# 5. Prometheus Dynamic Target Management
app.include_router(prometheus_targets.router)         # /api/v1/prometheus
#   - Register new scrape targets
#   - Update existing targets
#   - Delete target configurations

# 6. Log Aggregation (Grafana Loki)
app.include_router(logs.router)                       # /api/v1/logs
#   - Query Loki using LogQL
#   - Filter and search aggregated logs

# 7. Linux OS Management
app.include_router(linux_scripts.router)              # /api/v1/linux/execute
#   - Execute bash scripts securely
#   - Built-in safety blocks (prevents rm -rf /, etc.)

# 8. Interactive Terminal (WebSocket)
app.include_router(terminal.router)                   # /api/v1/linux/terminal
#   - Full PTY (Pseudo-Terminal) support
#   - Supports vim, top, htop, nano
#   - Real-time bidirectional communication
#   - Copy/Paste support via frontend

# 9. File Browser
app.include_router(file_browser.router)               # /api/v1/files
#   - List directory contents with metadata
#   - Upload files (single or multiple)
#   - Download files (streaming)
#   - Delete files/directories
#   - Rename/Move files/directories
#   - Create files/directories
#   - Read/Edit text files
#   - Path traversal protection
#   - Forbidden system paths blocked


# ------------------------------------------------------------------
# Root Endpoint (API Information)
# ------------------------------------------------------------------
@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "service": "Enterprise Linux Core Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
        "api_prefix": "/api/v1",
        "modules": [
            {"name": "auth", "path": "/api/v1/auth/login"},
            {"name": "metrics", "path": "/api/v1/metrics"},
            {"name": "services", "path": "/api/v1/services"},
            {"name": "oracle", "path": "/api/v1/oracle"},
            {"name": "mssql", "path": "/api/v1/mssql"},
            {"name": "prometheus", "path": "/api/v1/prometheus"},
            {"name": "logs", "path": "/api/v1/logs"},
            {"name": "linux", "path": "/api/v1/linux"},
            {"name": "files", "path": "/api/v1/files"},
        ]
    }
