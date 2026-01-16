from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from data.database import  init_database
from api.middleware import RateLimitMiddleware, LoggingMiddleware
from api.endpoints import health, file_review, pr_review
import structlog

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("startup_event")
    init_database()
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
    allow_origins=["*"], # Allow all for now, or specific GitHub domains per spec
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, limit=10, window=60)
# The spec says "10 req/min". I'll adjust to strict 10.
app.add_middleware(LoggingMiddleware)

# Routers
app.include_router(health.router)
app.include_router(file_review.router)
app.include_router(pr_review.router)

# Fix rate limit strictness
# Re-adding middleware with correct params if needed, 
# but FastAPI middleware stack is FIFO/LIFO. 
# I will edit the RateLimit line above to be limit=10.
