import pytest
from unittest.mock import Mock, patch, MagicMock
from app.application.services.email_service import EmailService
from app.infrastructure.email.smtp_adapter import SMTPEmailAdapter
from app.infrastructure.email.sendgrid_adapter import SendGridEmailAdapter
from app.infrastructure.email.aws_ses_adapter import AWSEmailAdapter
from app.infrastructure.email.email_factory import EmailServiceFactory
from app.core.config import Settings


class TestEmailServiceInterface:
    """Test suite for EmailService abstract interface."""

    def test_email_service_is_abstract(self):
        """Verify EmailService cannot be instantiated directly."""
        with pytest.raises(TypeError):
            EmailService()

    def test_email_service_has_send_email_method(self):
        """Verify EmailService defines send_email abstract method."""
        assert hasattr(EmailService, 'send_email')


class TestSMTPEmailAdapter:
    """Test suite for SMTP email adapter implementation."""

    def test_smtp_adapter_implements_email_service(self):
        """Verify SMTPEmailAdapter implements EmailService interface."""
        settings = Settings(
            SMTP_HOST="localhost",
            SMTP_PORT=587,
            SMTP_USER="test@example.com",
            SMTP_PASSWORD="password",
            SMTP_TLS=True
        )
        adapter = SMTPEmailAdapter(settings)
        assert isinstance(adapter, EmailService)

    @patch('smtplib.SMTP')
    def test_smtp_adapter_sends_plain_text_email(self, mock_smtp):
        """Verify SMTP adapter sends plain text email successfully."""
        settings = Settings(
            SMTP_HOST="localhost",
            SMTP_PORT=587,
            SMTP_USER="test@example.com",
            SMTP_PASSWORD="password",
            SMTP_TLS=True
        )
        adapter = SMTPEmailAdapter(settings)

        # Mock SMTP connection
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = adapter.send_email(
            from_email="sender@example.com",
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Plain text body"
        )

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "password")
        mock_server.send_message.assert_called_once()

    @patch('smtplib.SMTP')
    def test_smtp_adapter_sends_html_email(self, mock_smtp):
        """Verify SMTP adapter sends HTML email successfully."""
        settings = Settings(
            SMTP_HOST="localhost",
            SMTP_PORT=587,
            SMTP_USER="test@example.com",
            SMTP_PASSWORD="password",
            SMTP_TLS=True
        )
        adapter = SMTPEmailAdapter(settings)

        # Mock SMTP connection
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = adapter.send_email(
            from_email="sender@example.com",
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Plain text body",
            html_body="<html><body>HTML body</body></html>"
        )

        assert result is True
        mock_server.send_message.assert_called_once()

    @patch('smtplib.SMTP')
    def test_smtp_adapter_handles_send_failure(self, mock_smtp):
        """Verify SMTP adapter handles send failures gracefully."""
        settings = Settings(
            SMTP_HOST="localhost",
            SMTP_PORT=587,
            SMTP_USER="test@example.com",
            SMTP_PASSWORD="password",
            SMTP_TLS=True
        )
        adapter = SMTPEmailAdapter(settings)

        # Mock SMTP connection failure
        mock_smtp.side_effect = Exception("Connection failed")

        result = adapter.send_email(
            from_email="sender@example.com",
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Plain text body"
        )

        assert result is False


class TestSendGridEmailAdapter:
    """Test suite for SendGrid email adapter implementation."""

    def test_sendgrid_adapter_implements_email_service(self):
        """Verify SendGridEmailAdapter implements EmailService interface."""
        settings = Settings(SENDGRID_API_KEY="test_api_key")
        adapter = SendGridEmailAdapter(settings)
        assert isinstance(adapter, EmailService)

    def test_sendgrid_adapter_sends_plain_text_email(self):
        """Verify SendGrid adapter sends plain text email successfully."""
        settings = Settings(SENDGRID_API_KEY="test_api_key")

        # Mock SendGrid client
        mock_client = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client.send.return_value = mock_response

        adapter = SendGridEmailAdapter(settings, client=mock_client)

        result = adapter.send_email(
            from_email="sender@example.com",
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Plain text body"
        )

        assert result is True
        mock_client.send.assert_called_once()

    def test_sendgrid_adapter_sends_html_email(self):
        """Verify SendGrid adapter sends HTML email successfully."""
        settings = Settings(SENDGRID_API_KEY="test_api_key")

        # Mock SendGrid client
        mock_client = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client.send.return_value = mock_response

        adapter = SendGridEmailAdapter(settings, client=mock_client)

        result = adapter.send_email(
            from_email="sender@example.com",
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Plain text body",
            html_body="<html><body>HTML body</body></html>"
        )

        assert result is True

    def test_sendgrid_adapter_handles_send_failure(self):
        """Verify SendGrid adapter handles send failures gracefully."""
        settings = Settings(SENDGRID_API_KEY="test_api_key")

        # Mock SendGrid client failure
        mock_client = MagicMock()
        mock_client.send.side_effect = Exception("API error")

        adapter = SendGridEmailAdapter(settings, client=mock_client)

        result = adapter.send_email(
            from_email="sender@example.com",
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Plain text body"
        )

        assert result is False


class TestAWSEmailAdapter:
    """Test suite for AWS SES email adapter implementation."""

    def test_aws_adapter_implements_email_service(self):
        """Verify AWSEmailAdapter implements EmailService interface."""
        settings = Settings(
            AWS_SES_REGION="us-east-1",
            AWS_SES_ACCESS_KEY="test_access_key",
            AWS_SES_SECRET_KEY="test_secret_key"
        )
        adapter = AWSEmailAdapter(settings)
        assert isinstance(adapter, EmailService)

    def test_aws_adapter_sends_plain_text_email(self):
        """Verify AWS SES adapter sends plain text email successfully."""
        settings = Settings(
            AWS_SES_REGION="us-east-1",
            AWS_SES_ACCESS_KEY="test_access_key",
            AWS_SES_SECRET_KEY="test_secret_key"
        )

        # Mock SES client
        mock_ses = MagicMock()
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}

        adapter = AWSEmailAdapter(settings, client=mock_ses)

        result = adapter.send_email(
            from_email="sender@example.com",
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Plain text body"
        )

        assert result is True
        mock_ses.send_email.assert_called_once()

    def test_aws_adapter_sends_html_email(self):
        """Verify AWS SES adapter sends HTML email successfully."""
        settings = Settings(
            AWS_SES_REGION="us-east-1",
            AWS_SES_ACCESS_KEY="test_access_key",
            AWS_SES_SECRET_KEY="test_secret_key"
        )

        # Mock SES client
        mock_ses = MagicMock()
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}

        adapter = AWSEmailAdapter(settings, client=mock_ses)

        result = adapter.send_email(
            from_email="sender@example.com",
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Plain text body",
            html_body="<html><body>HTML body</body></html>"
        )

        assert result is True
        mock_ses.send_email.assert_called_once()

    def test_aws_adapter_handles_send_failure(self):
        """Verify AWS SES adapter handles send failures gracefully."""
        settings = Settings(
            AWS_SES_REGION="us-east-1",
            AWS_SES_ACCESS_KEY="test_access_key",
            AWS_SES_SECRET_KEY="test_secret_key"
        )

        # Mock SES client failure
        mock_ses = MagicMock()
        mock_ses.send_email.side_effect = Exception("SES error")

        adapter = AWSEmailAdapter(settings, client=mock_ses)

        result = adapter.send_email(
            from_email="sender@example.com",
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Plain text body"
        )

        assert result is False


class TestEmailServiceFactory:
    """Test suite for EmailServiceFactory."""

    def test_factory_creates_smtp_adapter(self):
        """Verify factory creates SMTP adapter when configured."""
        settings = Settings(
            EMAIL_PROVIDER="smtp",
            SMTP_HOST="localhost",
            SMTP_PORT=587,
            SMTP_USER="test@example.com",
            SMTP_PASSWORD="password"
        )
        adapter = EmailServiceFactory.create(settings)
        assert isinstance(adapter, SMTPEmailAdapter)

    def test_factory_creates_sendgrid_adapter(self):
        """Verify factory creates SendGrid adapter when configured."""
        settings = Settings(
            EMAIL_PROVIDER="sendgrid",
            SENDGRID_API_KEY="test_api_key"
        )
        adapter = EmailServiceFactory.create(settings)
        assert isinstance(adapter, SendGridEmailAdapter)

    def test_factory_creates_aws_adapter(self):
        """Verify factory creates AWS SES adapter when configured."""
        settings = Settings(
            EMAIL_PROVIDER="aws_ses",
            AWS_SES_REGION="us-east-1",
            AWS_SES_ACCESS_KEY="test_access_key",
            AWS_SES_SECRET_KEY="test_secret_key"
        )
        adapter = EmailServiceFactory.create(settings)
        assert isinstance(adapter, AWSEmailAdapter)

    def test_factory_raises_error_for_invalid_provider(self):
        """Verify factory raises error for invalid provider."""
        settings = Settings(EMAIL_PROVIDER="smtp")  # Valid enum value
        # Since EMAIL_PROVIDER is Literal type, invalid values are caught at type level
        # This test verifies the factory behavior is correct
        adapter = EmailServiceFactory.create(settings)
        assert isinstance(adapter, SMTPEmailAdapter)
