import sys
import time
import uuid
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Add parent directory to sys.path so 'backend' is always importable
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.db.session import init_db, check_db_health
from backend.retrieval.vector_store import vector_store
from backend.api import (
    documents_router,
    conversations_router,
    chat_router,
    auth_router,
    websockets_router,
    tools_router,
    seed_default_users
)

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database tables and ensure Qdrant collection
    logger.info("Initializing database schemas...")
    await init_db()
    await seed_default_users()
    logger.info("Verifying Qdrant vector store...")
    vector_store._ensure_collection()
    logger.info("Scanning for interrupted/zombie ingestion jobs...")
    from backend.workers import recover_zombie_jobs
    recovery_stats = await recover_zombie_jobs()
    if recovery_stats["recovered_jobs"] > 0 or recovery_stats["recovered_docs"] > 0:
        logger.info(f"Recovered zombie jobs: {recovery_stats}")
    logger.info("DocuChat backend started successfully.")
    yield
    logger.info("Shutting down DocuChat backend.")

app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description="Production Document Intelligence Platform with Hybrid Retrieval, WebSockets, and Multi-Tenancy",
    lifespan=lifespan
)

# Request ID & Structured Logging Middleware
@app.middleware("http")
async def request_correlation_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    
    # Structured access log (skipping spammy health checks in debug)
    if not request.url.path.endswith("/health"):
        logger.info(f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
    
    return response

# Structured Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = request.headers.get("X-Request-ID", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error_code": exc.status_code,
            "message": exc.detail,
            "request_id": request_id
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.error(f"[{request_id}] Unhandled server exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_code": 500,
            "message": "Internal server error occurred.",
            "request_id": request_id
        }
    )

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins in dev, configurable in settings.CORS_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(tools_router, prefix="/api")

# Mount Routers directly for backward compatibility
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(conversations_router)
app.include_router(chat_router)
app.include_router(tools_router)

# Mount WebSockets (root path)
app.include_router(websockets_router)

@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Liveness probe: verifies server process is responsive."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "llm_model": settings.LLM_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "router_mode": settings.ROUTER_MODE
    }

@app.get("/ready")
@app.get("/api/ready")
async def readiness_check():
    """Readiness probe: validates database connection and dependent services."""
    db_ok = await check_db_health()
    return {
        "status": "ready" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "vector_store": "initialized",
        "llm_model": settings.LLM_MODEL,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)

