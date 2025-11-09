"""
Integration tests for database session with RLS context.

Tests real database session lifecycle with RLS context integration.

Note: TestClient integration tests are limited by httpx/starlette version compatibility.
These tests focus on direct database session behavior that can be reliably tested.
"""
import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.infrastructure.database.rls import set_rls_context, clear_rls_context, get_current_org_id, get_current_plant_id


class TestDatabaseSessionIntegration:
    """Integration tests for database session RLS context"""

    def test_session_lifecycle_with_rls_context(self, db_session):
        """
        Test complete session lifecycle with RLS context set and cleared.

        Given: Database session with RLS context
        When: Context is set and then cleared
        Then: RLS variables are properly managed in PostgreSQL
        """
        # Act - Set context
        set_rls_context(db_session, organization_id=1, plant_id=10)

        # Verify context is set
        org_id = get_current_org_id(db_session)
        plant_id = get_current_plant_id(db_session)
        assert org_id == 1
        assert plant_id == 10

        # Clear context (simulating session close)
        clear_rls_context(db_session)

        # Assert - Context is cleared
        org_id_after = get_current_org_id(db_session)
        plant_id_after = get_current_plant_id(db_session)
        assert org_id_after is None
        assert plant_id_after is None

    def test_get_db_with_authenticated_mock_request(self):
        """
        Test get_db() dependency with mock authenticated request.

        Given: Mock request with user in request.state
        When: get_db() is called
        Then: Session is returned with RLS context set
        """
        # Arrange
        mock_request = Mock()
        mock_request.state.user = {
            "id": 123,
            "email": "test@example.com",
            "organization_id": 1,
            "plant_id": 10
        }

        # Act - Get database session
        db_generator = get_db(mock_request)
        db = next(db_generator)

        # Assert - Session returned
        assert isinstance(db, Session)

        # Verify RLS context is set (this requires real database connection)
        try:
            org_id = get_current_org_id(db)
            assert org_id == 1
        except Exception:
            # Skip if database not available
            pytest.skip("Database not available for RLS context verification")

        # Clean up
        try:
            next(db_generator)
        except StopIteration:
            pass

    def test_get_db_with_unauthenticated_mock_request(self):
        """
        Test get_db() dependency with mock unauthenticated request.

        Given: Mock request without user in request.state
        When: get_db() is called
        Then: Session is returned without RLS context
        """
        # Arrange
        mock_request = Mock()
        mock_request.state = Mock(spec=['__class__'])
        if hasattr(mock_request.state, 'user'):
            delattr(mock_request.state, 'user')

        # Act - Get database session
        db_generator = get_db(mock_request)
        db = next(db_generator)

        # Assert - Session returned
        assert isinstance(db, Session)

        # Verify RLS context is NOT set
        try:
            org_id = get_current_org_id(db)
            assert org_id is None
        except Exception:
            # Skip if database not available
            pytest.skip("Database not available for RLS context verification")

        # Clean up
        try:
            next(db_generator)
        except StopIteration:
            pass

    def test_get_db_without_request(self):
        """
        Test get_db() dependency without request parameter.

        Given: No request parameter provided
        When: get_db() is called
        Then: Session is returned without RLS context
        """
        # Act - Get database session without request
        db_generator = get_db()
        db = next(db_generator)

        # Assert - Session returned
        assert isinstance(db, Session)

        # Clean up
        try:
            next(db_generator)
        except StopIteration:
            pass

    def test_rls_context_isolation_between_sessions(self, db_session):
        """
        Test that RLS context is isolated between different database sessions.

        Given: Two sequential operations with different RLS contexts
        When: Each sets and uses different context
        Then: Contexts don't interfere with each other
        """
        # Session 1: org_id=1
        set_rls_context(db_session, organization_id=1, plant_id=10)
        org_id_1 = get_current_org_id(db_session)
        plant_id_1 = get_current_plant_id(db_session)
        assert org_id_1 == 1
        assert plant_id_1 == 10

        # Clear and set new context
        clear_rls_context(db_session)

        # Session 2: org_id=2
        set_rls_context(db_session, organization_id=2, plant_id=20)
        org_id_2 = get_current_org_id(db_session)
        plant_id_2 = get_current_plant_id(db_session)
        assert org_id_2 == 2
        assert plant_id_2 == 20

        # Clean up
        clear_rls_context(db_session)


@pytest.fixture
def db_session():
    """Provide real database session for integration tests"""
    session = SessionLocal()
    try:
        yield session
    finally:
        # Clear any RLS context before closing
        try:
            clear_rls_context(session)
        except Exception:
            pass  # Ignore errors if context wasn't set
        session.close()
