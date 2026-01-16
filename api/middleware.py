import time
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict

logger = structlog.get_logger()

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 10, window: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        # Clean old requests
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < self.window]
        
        if len(self.requests[client_ip]) >= self.limit:
            return Response("Too Many Requests", status_code=429)
            
        self.requests[client_ip].append(now)
        return await call_next(request)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", str(time.time()))
        
        logger.info("request_started", path=request.url.path, method=request.method, request_id=request_id)
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            logger.info(
                "request_completed", 
                path=request.url.path, 
                status=response.status_code, 
                duration=process_time
            )
            return response
        except Exception as e:
            logger.error("request_failed", error=str(e))
            raise e
