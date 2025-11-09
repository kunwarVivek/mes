"""
Unit tests for middleware components

Test Coverage:
- AuthMiddleware: JWT extraction, validation, RLS context setting
- RequestIDMiddleware: Request ID generation and header injection
- RateLimitMiddleware: Rate limit enforcement and tracking
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time
import uuid


class TestAuthMiddleware:
    """Test AuthMiddleware behavior"""

    @pytest.fixture
    def auth_middleware(self):
        from app.presentation.middleware.auth_middleware import AuthMiddleware
        mock_app = AsyncMock()
        return AuthMiddleware(mock_app)

    @pytest.fixture
    def mock_request(self):
        request = Mock(spec=Request)
        request.url.path = "/api/v1/users"
        request.headers = {}
        request.state = Mock()
        return request

    @pytest.mark.asyncio
    async def test_extracts_jwt_from_authorization_header(self, auth_middleware, mock_request):
        """Should extract JWT token from Authorization header"""
        mock_request.headers = {"authorization": "Bearer test_token_123"}

        # Mock the instance's jwt_handler
        mock_jwt = Mock()
        mock_jwt.decode_token.return_value = {
            "sub": "1",
            "email": "test@example.com",
            "organization_id": 1,
            "plant_id": None
        }
        auth_middleware.jwt_handler = mock_jwt

        # Middleware no longer creates DB session - just sets request.state
        await auth_middleware.dispatch(mock_request, AsyncMock())

        # Should call decode_token with extracted token
        mock_jwt.decode_token.assert_called_once_with("test_token_123")

        # Should set user in request state with RLS context
        assert hasattr(mock_request.state, 'user')
        assert mock_request.state.user['id'] == 1
        assert mock_request.state.user['email'] == "test@example.com"
        assert mock_request.state.user['organization_id'] == 1

    @pytest.mark.asyncio
    async def test_sets_rls_context_with_user_id(self, auth_middleware, mock_request):
        """Should set RLS context data in request.state for database dependency"""
        mock_request.headers = {"authorization": "Bearer test_token"}

        # Mock the instance's jwt_handler
        mock_jwt = Mock()
        mock_jwt.decode_token.return_value = {
            "sub": "42",
            "email": "user@example.com",
            "organization_id": 5,
            "plant_id": 10
        }
        auth_middleware.jwt_handler = mock_jwt

        # Middleware stores RLS context in request.state
        # Database dependency (get_db) will use this to set actual RLS context
        await auth_middleware.dispatch(mock_request, AsyncMock())

        # Should set user data with RLS context in request.state
        assert hasattr(mock_request.state, 'user')
        assert mock_request.state.user['id'] == 42
        assert mock_request.state.user['organization_id'] == 5
        assert mock_request.state.user['plant_id'] == 10

    @pytest.mark.asyncio
    async def test_returns_401_on_invalid_token(self, auth_middleware, mock_request):
        """Should return 401 Unauthorized for invalid JWT token"""
        mock_request.headers = {"authorization": "Bearer invalid_token"}

        # Mock the instance's jwt_handler to raise ValueError
        mock_jwt = Mock()
        mock_jwt.decode_token.side_effect = ValueError("Invalid token")
        auth_middleware.jwt_handler = mock_jwt

        response = await auth_middleware.dispatch(mock_request, AsyncMock())

        assert isinstance(response, JSONResponse)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_bypasses_public_endpoints(self, auth_middleware, mock_request):
        """Should bypass authentication for public endpoints"""
        public_paths = ["/health", "/docs", "/openapi.json", "/api/v1/auth/login"]

        for path in public_paths:
            mock_request.url.path = path
            mock_request.headers = {}  # No Authorization header

            call_next = AsyncMock(return_value=Response(status_code=200))
            response = await auth_middleware.dispatch(mock_request, call_next)

            # Should call next middleware without authentication
            call_next.assert_called_once()
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_401_on_missing_authorization_header(self, auth_middleware, mock_request):
        """Should return 401 when Authorization header is missing for protected routes"""
        mock_request.url.path = "/api/v1/users"
        mock_request.headers = {}  # No Authorization header

        response = await auth_middleware.dispatch(mock_request, AsyncMock())

        assert isinstance(response, JSONResponse)
        assert response.status_code == 401


class TestRequestIDMiddleware:
    """Test RequestIDMiddleware behavior"""

    @pytest.fixture
    def request_id_middleware(self):
        from app.presentation.middleware.request_id_middleware import RequestIDMiddleware
        mock_app = AsyncMock()
        return RequestIDMiddleware(mock_app)

    @pytest.fixture
    def mock_request(self):
        request = Mock(spec=Request)
        request.headers = {}
        request.state = Mock()
        return request

    @pytest.mark.asyncio
    async def test_adds_request_id_to_response_headers(self, request_id_middleware, mock_request):
        """Should add X-Request-ID header to response"""
        mock_response = Response(status_code=200)
        call_next = AsyncMock(return_value=mock_response)

        response = await request_id_middleware.dispatch(mock_request, call_next)

        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0

    @pytest.mark.asyncio
    async def test_generates_unique_request_ids(self, request_id_middleware):
        """Should generate unique request IDs for different requests"""
        # Create separate mock requests to ensure state isolation
        mock_request_1 = Mock(spec=Request)
        mock_request_1.headers = {}
        mock_request_1.state = Mock()

        mock_request_2 = Mock(spec=Request)
        mock_request_2.headers = {}
        mock_request_2.state = Mock()

        mock_response = Response(status_code=200)
        call_next = AsyncMock(return_value=mock_response)

        response1 = await request_id_middleware.dispatch(mock_request_1, call_next)

        # Need fresh response for second request
        mock_response2 = Response(status_code=200)
        call_next2 = AsyncMock(return_value=mock_response2)
        response2 = await request_id_middleware.dispatch(mock_request_2, call_next2)

        request_id_1 = response1.headers["x-request-id"]
        request_id_2 = response2.headers["x-request-id"]

        assert request_id_1 != request_id_2

    @pytest.mark.asyncio
    async def test_stores_request_id_in_state(self, request_id_middleware, mock_request):
        """Should store request_id in request.state for logging"""
        mock_response = Response(status_code=200)
        call_next = AsyncMock(return_value=mock_response)

        await request_id_middleware.dispatch(mock_request, call_next)

        assert hasattr(mock_request.state, 'request_id')
        # Validate UUID format
        uuid.UUID(mock_request.state.request_id)


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware behavior"""

    @pytest.fixture
    def rate_limit_middleware(self):
        from app.presentation.middleware.rate_limit_middleware import RateLimitMiddleware
        mock_app = AsyncMock()
        return RateLimitMiddleware(mock_app)

    @pytest.fixture
    def mock_request(self):
        request = Mock(spec=Request)
        request.url.path = "/api/v1/users"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        return request

    @pytest.mark.asyncio
    async def test_allows_requests_under_general_limit(self, rate_limit_middleware, mock_request):
        """Should allow requests under 100 req/min general limit"""
        call_next = AsyncMock(return_value=Response(status_code=200))

        # Make 50 requests (under limit)
        for _ in range(50):
            response = await rate_limit_middleware.dispatch(mock_request, call_next)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_429_when_general_limit_exceeded(self, rate_limit_middleware, mock_request):
        """Should return 429 Too Many Requests when general limit exceeded"""
        call_next = AsyncMock(return_value=Response(status_code=200))

        # Make 101 requests (exceed 100 req/min limit)
        for i in range(101):
            response = await rate_limit_middleware.dispatch(mock_request, call_next)

            if i < 100:
                assert response.status_code == 200
            else:
                assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_enforces_mutation_rate_limit(self, rate_limit_middleware, mock_request):
        """Should enforce 10 req/min limit for mutation endpoints"""
        mock_request.method = "POST"
        call_next = AsyncMock(return_value=Response(status_code=201))

        # Make 11 POST requests (exceed 10 req/min mutation limit)
        for i in range(11):
            response = await rate_limit_middleware.dispatch(mock_request, call_next)

            if i < 10:
                assert response.status_code == 201
            else:
                assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_rate_limit_per_client_ip(self, rate_limit_middleware):
        """Should track rate limits separately per client IP"""
        call_next = AsyncMock(return_value=Response(status_code=200))

        # Client 1 makes 100 requests
        request_1 = Mock(spec=Request)
        request_1.url.path = "/api/v1/users"
        request_1.method = "GET"
        request_1.client.host = "192.168.1.1"

        for _ in range(100):
            response = await rate_limit_middleware.dispatch(request_1, call_next)
            assert response.status_code == 200

        # Client 2 should still be allowed (different IP)
        request_2 = Mock(spec=Request)
        request_2.url.path = "/api/v1/users"
        request_2.method = "GET"
        request_2.client.host = "192.168.1.2"

        response = await rate_limit_middleware.dispatch(request_2, call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_includes_retry_after_header_on_429(self, rate_limit_middleware, mock_request):
        """Should include Retry-After header in 429 response"""
        call_next = AsyncMock(return_value=Response(status_code=200))

        # Exceed rate limit
        for _ in range(101):
            response = await rate_limit_middleware.dispatch(mock_request, call_next)

        # Last response should be 429 with Retry-After header
        assert response.status_code == 429
        assert "retry-after" in response.headers
        assert int(response.headers["retry-after"]) > 0
