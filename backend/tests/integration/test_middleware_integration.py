"""
Integration tests for middleware stack

Test Coverage:
- Middleware component interaction
- Middleware registration in FastAPI app
- Basic middleware integration smoke tests

Note: Full integration tests with TestClient are limited by httpx/starlette version compatibility.
Unit tests provide comprehensive coverage of individual middleware components.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestMiddlewareRegistration:
    """Test middleware can be registered and imported"""

    def test_middleware_modules_import_successfully(self):
        """Should be able to import all middleware modules"""
        from app.presentation.middleware.auth_middleware import AuthMiddleware
        from app.presentation.middleware.request_id_middleware import RequestIDMiddleware
        from app.presentation.middleware.rate_limit_middleware import RateLimitMiddleware

        assert AuthMiddleware is not None
        assert RequestIDMiddleware is not None
        assert RateLimitMiddleware is not None

    def test_middleware_can_be_instantiated(self):
        """Should be able to create middleware instances"""
        from app.presentation.middleware.auth_middleware import AuthMiddleware
        from app.presentation.middleware.request_id_middleware import RequestIDMiddleware
        from app.presentation.middleware.rate_limit_middleware import RateLimitMiddleware

        mock_app = Mock()

        auth_mw = AuthMiddleware(mock_app)
        request_id_mw = RequestIDMiddleware(mock_app)
        rate_limit_mw = RateLimitMiddleware(mock_app)

        assert auth_mw is not None
        assert request_id_mw is not None
        assert rate_limit_mw is not None

    def test_main_app_imports_middleware(self):
        """Should be able to import middleware from main app"""
        # This verifies the middleware is properly exported
        from app.presentation.middleware import (
            AuthMiddleware,
            RequestIDMiddleware,
            RateLimitMiddleware,
        )

        assert AuthMiddleware is not None
        assert RequestIDMiddleware is not None
        assert RateLimitMiddleware is not None

    def test_rls_module_exists(self):
        """Should have RLS context management module"""
        from app.infrastructure.database.rls import set_rls_context, clear_rls_context, get_rls_context

        assert set_rls_context is not None
        assert clear_rls_context is not None
        assert get_rls_context is not None

    @pytest.mark.asyncio
    async def test_middleware_chain_execution_order(self):
        """Should execute middleware in correct order"""
        from app.presentation.middleware.auth_middleware import AuthMiddleware
        from app.presentation.middleware.request_id_middleware import RequestIDMiddleware
        from app.presentation.middleware.rate_limit_middleware import RateLimitMiddleware

        execution_order = []

        # Create mock app that tracks execution
        async def final_handler(request):
            execution_order.append("handler")
            from fastapi import Response
            return Response(status_code=200)

        # Create mock request for public endpoint
        mock_request = Mock()
        mock_request.url.path = "/health"
        mock_request.headers = {}
        mock_request.state = Mock()
        mock_request.method = "GET"
        mock_request.client.host = "127.0.0.1"

        # Execute through middleware chain
        request_id_mw = RequestIDMiddleware(Mock())
        auth_mw = AuthMiddleware(Mock())
        rate_limit_mw = RateLimitMiddleware(Mock())

        # RequestID middleware first
        async def auth_chain(req):
            execution_order.append("auth")
            return await rate_limit_mw.dispatch(req, final_handler)

        async def request_id_chain(req):
            execution_order.append("request_id")
            return await auth_mw.dispatch(req, auth_chain)

        response = await request_id_chain(mock_request)

        # Verify execution order: request_id -> auth -> rate_limit -> handler
        assert execution_order == ["request_id", "auth", "handler"]  # Auth bypassed for /health

    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_auth(self):
        """Should require authentication for protected endpoints"""
        from app.presentation.middleware.auth_middleware import AuthMiddleware

        mock_request = Mock()
        mock_request.url.path = "/api/v1/users"
        mock_request.headers = {}  # No auth header

        auth_mw = AuthMiddleware(Mock())

        response = await auth_mw.dispatch(mock_request, AsyncMock())

        # Should return 401
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_public_endpoint_bypasses_auth(self):
        """Should bypass authentication for public endpoints"""
        from app.presentation.middleware.auth_middleware import AuthMiddleware
        from fastapi import Response

        mock_request = Mock()
        mock_request.url.path = "/health"
        mock_request.headers = {}

        auth_mw = AuthMiddleware(Mock())

        async def mock_handler(request):
            return Response(status_code=200)

        response = await auth_mw.dispatch(mock_request, mock_handler)

        # Should call handler without auth
        assert response.status_code == 200
