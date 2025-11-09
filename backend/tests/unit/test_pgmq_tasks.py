import pytest
from unittest.mock import patch, MagicMock
from app.infrastructure.messaging.pgmq_tasks import (
    process_user_task,
    send_welcome_email,
    cleanup_inactive_users,
    generate_user_report,
    get_pgmq_client
)


class TestPGMQTasks:
    """Unit tests for PGMQ task handlers"""

    def test_send_welcome_email_returns_success(self):
        """Test send_welcome_email task handler"""
        result = send_welcome_email(
            user_email="test@example.com",
            username="John Doe"
        )

        assert result["status"] == "sent"
        assert result["email"] == "test@example.com"

    def test_cleanup_inactive_users_returns_completed(self):
        """Test cleanup_inactive_users task handler"""
        result = cleanup_inactive_users()

        assert result["status"] == "completed"
        assert "users_processed" in result

    def test_generate_user_report_returns_report_url(self):
        """Test generate_user_report task handler"""
        result = generate_user_report(user_id=123)

        assert result["status"] == "completed"
        assert result["user_id"] == 123
        assert "report_url" in result

    def test_process_user_task_dispatches_send_welcome_email(self):
        """Test process_user_task dispatches to send_welcome_email"""
        message = {
            "task": "send_welcome_email",
            "email": "test@example.com",
            "username": "John"
        }

        result = process_user_task(message)

        assert result["status"] == "sent"
        assert result["email"] == "test@example.com"

    def test_process_user_task_dispatches_cleanup(self):
        """Test process_user_task dispatches to cleanup_inactive_users"""
        message = {
            "task": "cleanup_inactive_users"
        }

        result = process_user_task(message)

        assert result["status"] == "completed"

    def test_process_user_task_dispatches_report(self):
        """Test process_user_task dispatches to generate_user_report"""
        message = {
            "task": "generate_user_report",
            "user_id": 456
        }

        result = process_user_task(message)

        assert result["status"] == "completed"
        assert result["user_id"] == 456

    def test_process_user_task_raises_on_unknown_task(self):
        """Test process_user_task raises ValueError for unknown task"""
        message = {
            "task": "unknown_task_type"
        }

        with pytest.raises(ValueError, match="Unknown task type"):
            process_user_task(message)

    def test_get_pgmq_client_returns_configured_client(self):
        """Test get_pgmq_client returns properly configured client"""
        with patch("app.infrastructure.messaging.pgmq_tasks.PGMQClient") as mock_client:
            client = get_pgmq_client()

            # Verify client was created with settings
            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args.kwargs
            assert "host" in call_kwargs
            assert "port" in call_kwargs
            assert "database" in call_kwargs
            assert "user" in call_kwargs
            assert "password" in call_kwargs
            assert "max_retries" in call_kwargs
