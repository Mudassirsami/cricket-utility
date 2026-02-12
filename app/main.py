import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import uuid
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import engine, Base, AsyncSessionLocal
from app.routers import match_router, upcoming_router, finance_router, notification_router
from app.middleware import SecurityHeadersMiddleware, RateLimitMiddleware, InputValidationMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

settings = get_settings()
start_time = time.time()

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Cricket Club Management System")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        logger.info("Database tables checked/created successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't crash the app, just log the error
        pass
    yield
    # Shutdown
    logger.info("Shutting down Cricket Club Management System")

app = FastAPI(
    title="Cricket Club Management System",
    version="1.0.0",
    description="Production-grade cricket club management API with PIN-based role security.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, limiter=limiter)
app.add_middleware(InputValidationMiddleware)

# Production CORS configuration
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "https://yourdomain.com",  # Replace with your actual domain
]

# Always allow the deployed app URL
if settings.ENVIRONMENT == "production":
    allowed_origins.append("*")  # Allow all origins for Swagger docs

if settings.ENVIRONMENT == "development":
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(
        f"Request: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s - "
        f"ID: {request_id}"
    )
    
    return response


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.error(
        f"Unhandled exception - Request ID: {request_id} - "
        f"Path: {request.url.path} - Error: {str(exc)}",
        exc_info=True
    )
    
    if settings.ENVIRONMENT == "development":
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error.",
                "request_id": request_id,
                "error": str(exc)
            },
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error.",
            "request_id": request_id
        },
    )


app.include_router(match_router.router)
app.include_router(upcoming_router.router)
app.include_router(finance_router.router)
app.include_router(notification_router.router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/api/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Health check endpoint with system status"""
    try:
        # Check database connection
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "ok" if db_status == "healthy" else "error",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "request_id": getattr(request.state, 'request_id', 'unknown')
    }


@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "Cricket Club Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/metrics")
@limiter.limit("30/minute")
async def metrics(request: Request):
    """Basic metrics endpoint"""
    return {
        "timestamp": time.time(),
        "uptime": time.time() - start_time,
        "environment": settings.ENVIRONMENT,
        "database_url_type": "postgresql" if "postgresql" in settings.DATABASE_URL else "sqlite"
    }
