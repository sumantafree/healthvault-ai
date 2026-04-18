"""
HealthVault AI — FastAPI Application Entry Point
"""
import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import engine
from models import (  # noqa: F401 — ensure all models are registered
    AIInsight,
    FamilyMember,
    HealthMetric,
    HealthReport,
    Medicine,
    NotificationLog,
    Prescription,
    Reminder,
    User,
)
from routes import auth, family, insights, medicines, metrics, prescriptions, reminders, reports
from scheduler import start_scheduler, stop_scheduler

# ── Logger ─────────────────────────────────────────────────────────────────────

log = structlog.get_logger()

# ── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("HealthVault AI starting", env=settings.APP_ENV, version=settings.APP_VERSION)
    start_scheduler()
    yield
    stop_scheduler()
    await engine.dispose()
    log.info("HealthVault AI shutdown complete")


# ── App Factory ────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Family Health Intelligence Platform — track health metrics, "
        "upload reports, and receive AI-powered insights."
    ),
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)


# ── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    """Log request timing for every API call."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    log.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms,
    )
    response.headers["X-Response-Time"] = f"{duration_ms}ms"
    return response


# ── Global Exception Handler ───────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=request.url.path, error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# ── Routers ────────────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(family.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)
app.include_router(metrics.router, prefix=API_PREFIX)
app.include_router(insights.router, prefix=API_PREFIX)
app.include_router(prescriptions.router, prefix=API_PREFIX)
app.include_router(medicines.router, prefix=API_PREFIX)
app.include_router(reminders.router, prefix=API_PREFIX)


# ── Health Check ───────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"], summary="Health check")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
    }


@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    return {"message": f"Welcome to {settings.APP_NAME} API", "docs": "/docs"}
