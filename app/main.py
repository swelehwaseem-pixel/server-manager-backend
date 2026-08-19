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

# 🔥 Import all routers
from app.routers import (
    metrics,
    services,
    oracle_admin,
    prometheus_targets,
    mssql_admin,
    logs
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
    lifespan=lifespan
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
# Include All Routers (Full Suite)
# ------------------------------------------------------------------
app.include_router(metrics.router)                    # /api/v1/metrics
app.include_router(services.router)                   # /api/v1/services
app.include_router(oracle_admin.router)               # /api/v1/oracle
app.include_router(prometheus_targets.router)         # /api/v1/prometheus (Dynamic Targets)
app.include_router(mssql_admin.router)                # /api/v1/mssql
app.include_router(logs.router)                       # /api/v1/logs (Loki Proxy)
