from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from data.database import init_database
from api.middleware import RateLimitMiddleware, LoggingMiddleware
from api.endpoints import health, file_review, pr_review, webhook
from monitoring import metrics
import structlog
import os
import warnings

# Suppress Pydantic V2 deprecation warnings from libraries
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", message=".*PydanticDeprecatedSince20.*")

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("startup_event")
    
    # Initialize DB (Safe to call repeatedly, verifies connection)
    try:
        init_database()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_init_failed", error=str(e))
        
    # Cache warming / Pre-checks
    if os.getenv("GEMINI_API_KEY"):
        logger.info("gemini_key_detected")
    else:
        logger.warning("gemini_key_missing")
        
    yield
    # Shutdown
    logger.info("shutdown_event")

app = FastAPI(
    title="Code Review CrewAI API",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Production Middleware
app.add_middleware(RateLimitMiddleware, limit=10, window=60)
app.add_middleware(LoggingMiddleware)

# Routers
app.include_router(health.router)
app.include_router(metrics.router) # Production Metrics
app.include_router(file_review.router)
app.include_router(pr_review.router)
app.include_router(webhook.router)

