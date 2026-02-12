import logging
import time
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting with IP tracking"""
    
    def __init__(self, app, limiter: Limiter):
        super().__init__(app)
        self.limiter = limiter
        self.ip_requests = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = get_remote_address(request)
        current_time = time.time()
        
        # Clean old entries (older than 1 hour)
        cutoff_time = current_time - 3600
        self.ip_requests = {
            ip: reqs for ip, reqs in self.ip_requests.items()
            if any(req_time > cutoff_time for req_time in reqs)
        }
        
        # Track requests
        if client_ip not in self.ip_requests:
            self.ip_requests[client_ip] = []
        self.ip_requests[client_ip].append(current_time)
        
        # Check for abuse (more than 1000 requests per hour)
        if len(self.ip_requests[client_ip]) > 1000:
            logger.warning(f"Rate limit abuse detected from IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        return await call_next(request)

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize input data"""
    
    async def dispatch(self, request: Request, call_next):
        # Log suspicious activity
        if any(suspicious in request.url.path.lower() for suspicious in ['<script', 'javascript:', 'data:']):
            logger.warning(f"Suspicious request path detected: {request.url.path}")
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request entity too large"
            )
        
        return await call_next(request)
