"""
Rate Limit Middleware

Enforces rate limiting per client IP with separate limits for mutations.
Single Responsibility: Rate limiting and request throttling.

Optimizations:
- Periodic cleanup of expired client data
- Memory-efficient deque storage
- Fast path for under-limit requests
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Awaitable, Dict, List
from collections import defaultdict, deque
import time


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate Limit Middleware

    Responsibilities:
    - Enforce general rate limit (100 req/min)
    - Enforce mutation rate limit (10 req/min for POST/PUT/PATCH/DELETE)
    - Track limits per client IP
    - Return 429 Too Many Requests when limit exceeded
    - Include Retry-After header in 429 responses

    Performance:
    - O(1) amortized for request tracking
    - O(n) cleanup where n = requests in window
    - Periodic memory cleanup for inactive IPs
    """

    # Rate limits
    GENERAL_LIMIT = 100  # requests per minute
    MUTATION_LIMIT = 10  # requests per minute for mutations
    WINDOW_SIZE = 60  # seconds (1 minute)
    CLEANUP_INTERVAL = 300  # Clean inactive IPs every 5 minutes

    # Mutation methods
    MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, app):
        super().__init__(app)
        # Track requests per IP: {ip: deque([timestamp1, timestamp2, ...])}
        self.general_requests: Dict[str, deque] = defaultdict(deque)
        self.mutation_requests: Dict[str, deque] = defaultdict(deque)
        self.last_cleanup = time.time()

    def _clean_old_requests(self, request_queue: deque, current_time: float) -> None:
        """Remove requests outside the time window"""
        cutoff_time = current_time - self.WINDOW_SIZE

        while request_queue and request_queue[0] < cutoff_time:
            request_queue.popleft()

    def _is_rate_limited(
        self,
        client_ip: str,
        is_mutation: bool,
        current_time: float
    ) -> tuple[bool, int]:
        """
        Check if client is rate limited

        Returns:
            (is_limited, retry_after_seconds)
        """
        # Choose appropriate request queue and limit
        if is_mutation:
            request_queue = self.mutation_requests[client_ip]
            limit = self.MUTATION_LIMIT
        else:
            request_queue = self.general_requests[client_ip]
            limit = self.GENERAL_LIMIT

        # Clean old requests outside time window
        self._clean_old_requests(request_queue, current_time)

        # Check if limit exceeded
        if len(request_queue) >= limit:
            # Calculate retry after (time until oldest request expires)
            oldest_request = request_queue[0]
            retry_after = int(oldest_request + self.WINDOW_SIZE - current_time) + 1
            return True, retry_after

        return False, 0

    def _record_request(self, client_ip: str, is_mutation: bool, current_time: float) -> None:
        """Record request timestamp for rate limiting"""
        # Record in general queue
        self.general_requests[client_ip].append(current_time)

        # Also record in mutation queue if applicable
        if is_mutation:
            self.mutation_requests[client_ip].append(current_time)

    def _cleanup_inactive_ips(self, current_time: float) -> None:
        """
        Remove IPs with no recent activity to prevent memory bloat

        Optimization: Periodic cleanup reduces memory usage for long-running servers
        """
        if current_time - self.last_cleanup < self.CLEANUP_INTERVAL:
            return

        cutoff_time = current_time - self.WINDOW_SIZE

        # Remove IPs with no requests in the window
        inactive_ips = [
            ip for ip, queue in self.general_requests.items()
            if not queue or queue[-1] < cutoff_time
        ]

        for ip in inactive_ips:
            del self.general_requests[ip]
            if ip in self.mutation_requests:
                del self.mutation_requests[ip]

        self.last_cleanup = current_time

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Process request through rate limit middleware

        Flow:
        1. Periodic cleanup (optimization)
        2. Get client IP
        3. Check if request is mutation
        4. Check general rate limit
        5. Check mutation rate limit (if applicable)
        6. Record request if not rate limited
        7. Call next middleware or return 429
        """
        # Get client IP and current time
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Periodic cleanup of inactive IPs (optimization)
        self._cleanup_inactive_ips(current_time)

        # Determine if this is a mutation request
        is_mutation = request.method in self.MUTATION_METHODS

        # Check general rate limit
        is_limited, retry_after = self._is_rate_limited(
            client_ip,
            is_mutation=False,
            current_time=current_time
        )

        if is_limited:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": str(retry_after)}
            )

        # Check mutation rate limit if applicable
        if is_mutation:
            is_limited, retry_after = self._is_rate_limited(
                client_ip,
                is_mutation=True,
                current_time=current_time
            )

            if is_limited:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many mutation requests. Please try again later."},
                    headers={"Retry-After": str(retry_after)}
                )

        # Record request
        self._record_request(client_ip, is_mutation, current_time)

        # Call next middleware
        return await call_next(request)
