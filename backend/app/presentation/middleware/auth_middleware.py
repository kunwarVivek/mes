"""
Authentication Middleware

Extracts JWT from Authorization header, validates token, and sets RLS context.
Single Responsibility: Authentication and RLS context management.

Optimizations:
- Early exit for public endpoints (fast path)
- Efficient header parsing
- Single database session for RLS context
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Awaitable
from app.infrastructure.security.jwt_handler import JWTHandler


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication Middleware

    Responsibilities:
    - Extract JWT from Authorization header
    - Validate JWT token
    - Set user information in request.state
    - Set RLS context in database session
    - Bypass authentication for public endpoints
    """

    # Public endpoints that don't require authentication
    PUBLIC_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    def __init__(self, app):
        super().__init__(app)
        self.jwt_handler = JWTHandler()

    def is_public_path(self, path: str) -> bool:
        """Check if path is public and doesn't require authentication"""
        # Exact match
        if path in self.PUBLIC_PATHS:
            return True

        # Auth endpoints (login, register, etc.)
        if path.startswith("/api/") and "/auth/" in path:
            return True

        return False

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Process request through authentication middleware

        Flow:
        1. Check if path is public -> skip authentication
        2. Extract Authorization header
        3. Validate JWT token
        4. Set user in request.state
        5. Set RLS context in database
        6. Call next middleware
        """
        # Bypass authentication for public paths
        if self.is_public_path(request.url.path):
            return await call_next(request)

        # Extract Authorization header
        auth_header = request.headers.get("authorization", "")

        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authorization header"}
            )

        # Extract token from "Bearer <token>" format
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format"}
            )

        token = parts[1]

        # Validate JWT token
        try:
            payload = self.jwt_handler.decode_token(token)
        except ValueError as e:
            return JSONResponse(
                status_code=401,
                content={"detail": str(e)}
            )

        # Extract user information from token
        user_id = int(payload.get("sub"))
        user_email = payload.get("email")
        organization_id = payload.get("organization_id")
        plant_id = payload.get("plant_id")

        # Store user info in request state for database dependency to use
        request.state.user = {
            "id": user_id,
            "email": user_email,
            "organization_id": organization_id,
            "plant_id": plant_id
        }

        # Database dependency (get_db) will handle RLS context setting
        # No need to create separate session in middleware

        # Call next middleware
        return await call_next(request)
