from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import engine, Base
from app.routers import match_router, upcoming_router, finance_router, notification_router

settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])

app = FastAPI(
    title="Cricket Club Management System",
    version="1.0.0",
    description="Production-grade cricket club management API with PIN-based role security.",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
    )


app.include_router(match_router.router)
app.include_router(upcoming_router.router)
app.include_router(finance_router.router)
app.include_router(notification_router.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
