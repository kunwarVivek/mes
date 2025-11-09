"""
JWT Tenant Context Tests - Multi-Tenant RLS Enforcement

Tests for JWT tenant context enhancement:
1. JWT tokens include organization_id and plant_id
2. Token decoding extracts tenant fields
3. Middleware sets PostgreSQL RLS session variables
4. Requests without tenant context return 403
5. Login returns tenant fields in response
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy import text
from fastapi import HTTPException

from app.infrastructure.security.jwt_handler import JWTHandler
from app.infrastructure.security.dependencies import get_current_user
from app.application.use_cases.auth.login_user import LoginUserUseCase
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username


class TestJWTTenantContext:
    """Test JWT includes tenant fields for RLS enforcement"""

    def test_create_access_token_includes_tenant_fields(self):
        """
        RED Test 1: JWT access token must include organization_id and plant_id

        This ensures RLS policies can enforce tenant isolation.
        """
        # Arrange
        jwt_handler = JWTHandler()
        token_data = {
            "sub": "1",
            "email": "user@example.com",
            "organization_id": 100,
            "plant_id": 200
        }

        # Act
        token = jwt_handler.create_access_token(token_data)
        decoded = jwt_handler.decode_token(token)

        # Assert
        assert decoded["sub"] == "1"
        assert decoded["email"] == "user@example.com"
        assert decoded["organization_id"] == 100, "JWT must include organization_id for RLS"
        assert decoded["plant_id"] == 200, "JWT must include plant_id for RLS"
        assert decoded["type"] == "access"

    def test_create_access_token_allows_null_plant_id(self):
        """
        RED Test 2: JWT must allow null plant_id (organization-level users)

        Some users work at organization level without specific plant assignment.
        """
        # Arrange
        jwt_handler = JWTHandler()
        token_data = {
            "sub": "2",
            "email": "admin@example.com",
            "organization_id": 100,
            "plant_id": None
        }

        # Act
        token = jwt_handler.create_access_token(token_data)
        decoded = jwt_handler.decode_token(token)

        # Assert
        assert decoded["organization_id"] == 100
        assert decoded.get("plant_id") is None

    def test_decode_token_extracts_tenant_fields(self):
        """
        RED Test 3: Decode token must extract organization_id and plant_id

        Middleware needs these fields to set PostgreSQL session variables.
        """
        # Arrange
        jwt_handler = JWTHandler()
        token_data = {
            "sub": "3",
            "email": "operator@example.com",
            "organization_id": 150,
            "plant_id": 250
        }
        token = jwt_handler.create_access_token(token_data)

        # Act
        payload = jwt_handler.decode_token(token)

        # Assert
        assert "organization_id" in payload, "Decoded token must include organization_id"
        assert "plant_id" in payload, "Decoded token must include plant_id"
        assert payload["organization_id"] == 150
        assert payload["plant_id"] == 250


class TestMiddlewareRLSEnforcement:
    """Test middleware sets PostgreSQL RLS session variables"""

    @pytest.mark.asyncio
    async def test_get_current_user_sets_rls_session_variables(self):
        """
        GREEN Test 4: Middleware must set PostgreSQL session variables for RLS

        Sets:
        - app.current_organization_id
        - app.current_plant_id
        """
        # Arrange
        jwt_handler = JWTHandler()
        token_data = {
            "sub": "4",
            "email": "worker@example.com",
            "organization_id": 300,
            "plant_id": 400
        }
        token = jwt_handler.create_access_token(token_data)

        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = token

        # Mock database session with proper call tracking
        mock_db = Mock()

        # Mock user repository
        mock_user = User(
            id=4,
            email=Email("worker@example.com"),
            username=Username("worker"),
            hashed_password="hashed",
            organization_id=300,
            plant_id=400,
            is_active=True
        )

        with patch('app.infrastructure.security.dependencies.UserRepository') as MockRepo:
            mock_repo_instance = MockRepo.return_value
            mock_repo_instance.get_by_id.return_value = mock_user

            # Act
            user = await get_current_user(mock_credentials, mock_db)

            # Assert
            assert user.id == 4

            # Verify db.execute was called (for RLS session variables)
            assert mock_db.execute.called, "db.execute must be called to set RLS variables"

            # Get all execute calls and extract SQL text
            execute_calls = []
            for call in mock_db.execute.call_args_list:
                # call is a tuple of (args, kwargs)
                args = call[0]
                if args:
                    # TextClause object has a 'text' attribute
                    sql_obj = args[0]
                    if hasattr(sql_obj, 'text'):
                        execute_calls.append(sql_obj.text)
                    else:
                        execute_calls.append(str(sql_obj))

            # Verify RLS session variables were set
            set_org_id = any("300" in call and "organization" in call.lower()
                           for call in execute_calls)
            set_plant_id = any("400" in call and "plant" in call.lower()
                            for call in execute_calls)

            assert set_org_id, f"Middleware must set app.current_organization_id for RLS. Calls: {execute_calls}"
            assert set_plant_id, f"Middleware must set app.current_plant_id for RLS. Calls: {execute_calls}"

    @pytest.mark.asyncio
    async def test_get_current_user_raises_403_if_no_organization_id(self):
        """
        RED Test 5: Middleware must reject tokens without organization_id

        All users MUST belong to an organization for RLS to work.
        """
        # Arrange
        jwt_handler = JWTHandler()
        # Token WITHOUT organization_id (security issue)
        token_data = {
            "sub": "5",
            "email": "hacker@example.com"
        }
        token = jwt_handler.create_access_token(token_data)

        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = token

        # Mock database session
        mock_db = MagicMock()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_db)

        assert exc_info.value.status_code == 403
        assert "organization_id" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_get_current_user_handles_null_plant_id(self):
        """
        GREEN Test 6: Middleware must handle users with null plant_id

        Organization-level users don't have plant assignments.
        """
        # Arrange
        jwt_handler = JWTHandler()
        token_data = {
            "sub": "6",
            "email": "orgadmin@example.com",
            "organization_id": 500,
            "plant_id": None
        }
        token = jwt_handler.create_access_token(token_data)

        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = token

        # Mock database session with proper call tracking
        mock_db = Mock()

        # Mock user repository
        mock_user = User(
            id=6,
            email=Email("orgadmin@example.com"),
            username=Username("orgadmin"),
            hashed_password="hashed",
            organization_id=500,
            plant_id=None,
            is_active=True
        )

        with patch('app.infrastructure.security.dependencies.UserRepository') as MockRepo:
            mock_repo_instance = MockRepo.return_value
            mock_repo_instance.get_by_id.return_value = mock_user

            # Act
            user = await get_current_user(mock_credentials, mock_db)

            # Assert
            assert user.id == 6
            assert user.organization_id == 500
            assert user.plant_id is None

            # Verify db.execute was called
            assert mock_db.execute.called, "db.execute must be called to set RLS variables"

            # Get all execute calls and extract SQL text
            execute_calls = []
            for call in mock_db.execute.call_args_list:
                args = call[0]
                if args:
                    sql_obj = args[0]
                    if hasattr(sql_obj, 'text'):
                        execute_calls.append(sql_obj.text)
                    else:
                        execute_calls.append(str(sql_obj))

            # Verify organization_id was set
            set_org_id = any("500" in call and "organization" in call.lower()
                           for call in execute_calls)
            assert set_org_id, f"Must set organization_id even when plant_id is null. Calls: {execute_calls}"

            # Verify plant_id was NOT set (since it's null)
            set_plant_id = any("plant" in call.lower() for call in execute_calls)
            assert not set_plant_id, f"Should NOT set plant_id when it's null. Calls: {execute_calls}"


class TestLoginTenantContext:
    """Test login returns tenant context"""

    def test_login_use_case_includes_tenant_in_token(self):
        """
        RED Test 7: Login use case must include tenant fields in JWT

        Frontend needs organization_id and plant_id for context.
        """
        # Arrange
        mock_user = User(
            id=7,
            email=Email("login@example.com"),
            username=Username("loginuser"),
            hashed_password="$2b$12$somehash",  # bcrypt hash format
            organization_id=600,
            plant_id=700,
            is_active=True
        )

        mock_repo = Mock()
        mock_repo.get_by_email.return_value = mock_user

        use_case = LoginUserUseCase(mock_repo)

        # Mock password verification
        with patch.object(use_case, '_verify_password', return_value=True):
            # Act
            token = use_case.execute("login@example.com", "password123")

            # Decode the access token to verify tenant fields
            jwt_handler = JWTHandler()
            decoded = jwt_handler.decode_token(token.access_token)

            # Assert
            assert decoded["organization_id"] == 600, "Login token must include organization_id"
            assert decoded["plant_id"] == 700, "Login token must include plant_id"

    def test_login_response_dto_includes_tenant_fields(self):
        """
        RED Test 8: Login response DTO must include tenant fields

        Frontend needs to know user's tenant context immediately after login.
        """
        # This test will verify the DTO structure
        # For now, we'll mark this as pending implementation
        pytest.skip("Will implement after DTO enhancement")


# Run tests to verify they FAIL (RED phase)
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
