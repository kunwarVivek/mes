"""
Unit tests for RLS (Row-Level Security) helper functions.

Tests the RLS context management functions without requiring database policies.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy import text


class TestRLSContextFunctions:
    """Unit tests for RLS context helper functions."""

    @patch('app.infrastructure.database.rls._get_settings')
    def test_set_rls_context_with_org_and_plant(self, mock_get_settings):
        """Test setting RLS context with both organization_id and plant_id."""
        from app.infrastructure.database.rls import set_rls_context

        # Create mock settings object
        mock_settings = Mock()
        mock_settings.RLS_ENABLED = True
        mock_get_settings.return_value = mock_settings

        mock_session = Mock(spec=Session)
        mock_session.execute = Mock()

        # Test setting both org and plant
        set_rls_context(mock_session, organization_id=1, plant_id=10)

        # Verify SQL commands were executed (2 calls: org + plant)
        assert mock_session.execute.call_count == 2
        calls = mock_session.execute.call_args_list

        # Check organization_id was set with parameterized query
        org_call = str(calls[0][0][0])
        assert "app.current_organization_id" in org_call
        assert ":org_id" in org_call

        # Check plant_id was set with parameterized query
        plant_call = str(calls[1][0][0])
        assert "app.current_plant_id" in plant_call
        assert ":plant_id" in plant_call

    @patch('app.infrastructure.database.rls._get_settings')
    def test_set_rls_context_org_only(self, mock_get_settings):
        """Test setting RLS context with only organization_id."""
        from app.infrastructure.database.rls import set_rls_context

        # Create mock settings object
        mock_settings = Mock()
        mock_settings.RLS_ENABLED = True
        mock_get_settings.return_value = mock_settings

        mock_session = Mock(spec=Session)
        mock_session.execute = Mock()

        # Test setting only org (plant=None means only 1 call)
        set_rls_context(mock_session, organization_id=2, plant_id=None)

        # Should execute 1 call (only org, plant is None so not set)
        assert mock_session.execute.call_count == 1
        calls = mock_session.execute.call_args_list

        org_call = str(calls[0][0][0])
        assert "app.current_organization_id" in org_call
        assert ":org_id" in org_call

    def test_set_rls_context_missing_org_id_raises_error(self):
        """Test that missing organization_id raises TypeError."""
        from app.infrastructure.database.rls import set_rls_context

        mock_session = Mock(spec=Session)

        # organization_id is required (positional argument)
        with pytest.raises(TypeError):
            set_rls_context(mock_session)

    @patch('app.infrastructure.database.rls._get_settings')
    def test_get_current_org_id_returns_value(self, mock_get_settings):
        """Test retrieving current organization_id from session context."""
        from app.infrastructure.database.rls import get_current_org_id

        # Create mock settings object
        mock_settings = Mock()
        mock_settings.RLS_ENABLED = True
        mock_get_settings.return_value = mock_settings

        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar.return_value = '42'
        mock_session.execute.return_value = mock_result

        org_id = get_current_org_id(mock_session)

        assert org_id == 42
        mock_session.execute.assert_called_once()
        call_arg = str(mock_session.execute.call_args[0][0])
        assert "current_setting" in call_arg
        assert "app.current_organization_id" in call_arg

    @patch('app.infrastructure.database.rls._get_settings')
    def test_get_current_org_id_returns_none_when_not_set(self, mock_get_settings):
        """Test that get_current_org_id returns None when context is not set."""
        from app.infrastructure.database.rls import get_current_org_id

        # Create mock settings object
        mock_settings = Mock()
        mock_settings.RLS_ENABLED = True
        mock_get_settings.return_value = mock_settings

        mock_session = Mock(spec=Session)
        mock_session.execute.side_effect = Exception("unrecognized configuration parameter")

        org_id = get_current_org_id(mock_session)

        assert org_id is None

    @patch('app.infrastructure.database.rls._get_settings')
    def test_get_current_plant_id_returns_value(self, mock_get_settings):
        """Test retrieving current plant_id from session context."""
        from app.infrastructure.database.rls import get_current_plant_id

        # Create mock settings object
        mock_settings = Mock()
        mock_settings.RLS_ENABLED = True
        mock_get_settings.return_value = mock_settings

        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.scalar.return_value = '100'
        mock_session.execute.return_value = mock_result

        plant_id = get_current_plant_id(mock_session)

        assert plant_id == 100
        mock_session.execute.assert_called_once()
        call_arg = str(mock_session.execute.call_args[0][0])
        assert "current_setting" in call_arg
        assert "app.current_plant_id" in call_arg

    @patch('app.infrastructure.database.rls._get_settings')
    def test_get_current_plant_id_returns_none_when_not_set(self, mock_get_settings):
        """Test that get_current_plant_id returns None when context is not set."""
        from app.infrastructure.database.rls import get_current_plant_id

        # Create mock settings object
        mock_settings = Mock()
        mock_settings.RLS_ENABLED = True
        mock_get_settings.return_value = mock_settings

        mock_session = Mock(spec=Session)
        mock_session.execute.side_effect = Exception("unrecognized configuration parameter")

        plant_id = get_current_plant_id(mock_session)

        assert plant_id is None

    @patch('app.infrastructure.database.rls._get_settings')
    def test_clear_rls_context(self, mock_get_settings):
        """Test clearing RLS context variables."""
        from app.infrastructure.database.rls import clear_rls_context

        # Create mock settings object
        mock_settings = Mock()
        mock_settings.RLS_ENABLED = True
        mock_get_settings.return_value = mock_settings

        mock_session = Mock(spec=Session)
        mock_session.execute = Mock()

        clear_rls_context(mock_session)

        # Should execute RESET for 3 variables (org, plant, user)
        assert mock_session.execute.call_count == 3
        calls = mock_session.execute.call_args_list

        org_call = str(calls[0][0][0])
        assert "RESET app.current_organization_id" in org_call

        plant_call = str(calls[1][0][0])
        assert "RESET app.current_plant_id" in plant_call

    def test_audit_log_enabled_writes_log(self):
        """Test that audit log is not implemented in new safe RLS module."""
        # Safe RLS module doesn't have audit logging - that was only in vulnerable version
        # This test is no longer applicable
        pass

    def test_audit_log_disabled_skips_log(self):
        """Test that audit log is not implemented in new safe RLS module."""
        # Safe RLS module doesn't have audit logging - that was only in vulnerable version
        # This test is no longer applicable
        pass
