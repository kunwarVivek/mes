"""
Unit tests for database session RLS context integration.

Tests the get_db() dependency with automatic RLS context management.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request
from sqlalchemy.orm import Session
from app.core.database import get_db


class TestDatabaseRLSIntegration:
    """Test database session with RLS context integration"""

    def test_get_db_sets_rls_context_for_authenticated_user(self):
        """
        Test that get_db() automatically sets RLS context when request has authenticated user.

        Given: Request with user in request.state (org_id=1, plant_id=10)
        When: get_db() dependency is invoked
        Then: RLS context is set with org_id=1, plant_id=10
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.state.user = {
            "id": 123,
            "email": "test@example.com",
            "organization_id": 1,
            "plant_id": 10
        }

        with patch('app.core.database.SessionLocal') as mock_session_local:
            with patch('app.core.database.set_rls_context') as mock_set_rls:
                mock_session = MagicMock(spec=Session)
                mock_session_local.return_value = mock_session

                # Act
                db_generator = get_db(mock_request)
                db = next(db_generator)

                # Assert
                assert db == mock_session
                mock_set_rls.assert_called_once_with(
                    mock_session,
                    organization_id=1,
                    plant_id=10
                )

    def test_get_db_handles_unauthenticated_requests(self):
        """
        Test that get_db() handles unauthenticated requests without setting RLS context.

        Given: Request without user in request.state
        When: get_db() dependency is invoked
        Then: No RLS context is set, session returned normally
        """
        # Arrange
        mock_request = Mock(spec=Request)
        # Explicitly set state without user attribute
        mock_request.state = Mock(spec=['__class__'])
        # Remove user attribute if it exists
        if hasattr(mock_request.state, 'user'):
            delattr(mock_request.state, 'user')

        with patch('app.core.database.SessionLocal') as mock_session_local:
            with patch('app.core.database.set_rls_context') as mock_set_rls:
                mock_session = MagicMock(spec=Session)
                mock_session_local.return_value = mock_session

                # Act
                db_generator = get_db(mock_request)
                db = next(db_generator)

                # Assert
                assert db == mock_session
                mock_set_rls.assert_not_called()

    def test_get_db_clears_rls_context_on_session_close(self):
        """
        Test that RLS context is cleared when database session closes.

        Given: Request with authenticated user (RLS context set)
        When: Database session closes (finally block)
        Then: clear_rls_context() is called
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.state.user = {
            "id": 123,
            "email": "test@example.com",
            "organization_id": 2,
            "plant_id": 20
        }

        with patch('app.core.database.SessionLocal') as mock_session_local:
            with patch('app.core.database.set_rls_context') as mock_set_rls:
                with patch('app.core.database.clear_rls_context') as mock_clear_rls:
                    mock_session = MagicMock(spec=Session)
                    mock_session_local.return_value = mock_session

                    # Act
                    db_generator = get_db(mock_request)
                    db = next(db_generator)

                    # Trigger finally block
                    try:
                        next(db_generator)
                    except StopIteration:
                        pass

                    # Assert
                    mock_set_rls.assert_called_once()
                    mock_clear_rls.assert_called_once_with(mock_session)
                    mock_session.close.assert_called_once()

    def test_get_db_handles_missing_organization_id(self):
        """
        Test that get_db() handles authenticated user without organization_id.

        Given: Request with user but no organization_id
        When: get_db() dependency is invoked
        Then: No RLS context is set (graceful handling)
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.state.user = {
            "id": 123,
            "email": "test@example.com"
            # No organization_id
        }

        with patch('app.core.database.SessionLocal') as mock_session_local:
            with patch('app.core.database.set_rls_context') as mock_set_rls:
                mock_session = MagicMock(spec=Session)
                mock_session_local.return_value = mock_session

                # Act
                db_generator = get_db(mock_request)
                db = next(db_generator)

                # Assert
                assert db == mock_session
                mock_set_rls.assert_not_called()

    def test_get_db_handles_optional_plant_id(self):
        """
        Test that get_db() handles user with org_id but no plant_id.

        Given: Request with user (org_id=3, no plant_id)
        When: get_db() dependency is invoked
        Then: RLS context set with org_id=3, plant_id=None
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.state.user = {
            "id": 123,
            "email": "test@example.com",
            "organization_id": 3
            # No plant_id
        }

        with patch('app.core.database.SessionLocal') as mock_session_local:
            with patch('app.core.database.set_rls_context') as mock_set_rls:
                mock_session = MagicMock(spec=Session)
                mock_session_local.return_value = mock_session

                # Act
                db_generator = get_db(mock_request)
                db = next(db_generator)

                # Assert
                assert db == mock_session
                mock_set_rls.assert_called_once_with(
                    mock_session,
                    organization_id=3,
                    plant_id=None
                )

    def test_get_db_logs_session_lifecycle(self):
        """
        Test that session lifecycle is logged (debug level).

        Given: Request with authenticated user
        When: get_db() creates and closes session
        Then: Lifecycle events are logged
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.state.user = {
            "id": 123,
            "email": "test@example.com",
            "organization_id": 1,
            "plant_id": 10
        }

        with patch('app.core.database.SessionLocal') as mock_session_local:
            with patch('app.core.database.set_rls_context'):
                with patch('app.core.database.clear_rls_context'):
                    with patch('app.core.database.logger') as mock_logger:
                        mock_session = MagicMock(spec=Session)
                        mock_session_local.return_value = mock_session

                        # Act
                        db_generator = get_db(mock_request)
                        db = next(db_generator)

                        try:
                            next(db_generator)
                        except StopIteration:
                            pass

                        # Assert - verify logging occurred
                        assert mock_logger.debug.call_count >= 2  # Session created + closed

    def test_get_db_handles_rls_context_errors_gracefully(self):
        """
        Test that get_db() handles RLS context errors without breaking session.

        Given: Request with authenticated user, but set_rls_context() raises error
        When: get_db() attempts to set RLS context
        Then: Error is logged, session still returned (degraded mode)
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.state.user = {
            "id": 123,
            "email": "test@example.com",
            "organization_id": 1,
            "plant_id": 10
        }

        with patch('app.core.database.SessionLocal') as mock_session_local:
            with patch('app.core.database.set_rls_context') as mock_set_rls:
                with patch('app.core.database.logger') as mock_logger:
                    mock_session = MagicMock(spec=Session)
                    mock_session_local.return_value = mock_session
                    mock_set_rls.side_effect = RuntimeError("RLS context error")

                    # Act
                    db_generator = get_db(mock_request)
                    db = next(db_generator)

                    # Assert - session still returned despite error
                    assert db == mock_session
                    mock_logger.warning.assert_called_once()
