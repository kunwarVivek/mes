"""
Request ID Middleware

Generates unique request IDs for request tracking and logging.
Single Responsibility: Request identification and tracking.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Awaitable
import uuid


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Request ID Middleware

    Responsibilities:
    - Generate unique request ID for each request
    - Add X-Request-ID header to response
    - Store request_id in request.state for logging
    """

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Process request through request ID middleware

        Flow:
        1. Generate unique request ID (UUID4)
        2. Store in request.state for logging/tracing
        3. Call next middleware
        4. Add X-Request-ID header to response
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store in request state for logging
        request.state.request_id = request_id

        # Call next middleware
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
