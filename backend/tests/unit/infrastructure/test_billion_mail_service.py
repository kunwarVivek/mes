"""Unit tests for Billion Mail email service."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from smtplib import SMTPException


def test_billion_mail_smtp_client_initialization():
    """Test BillionMailSMTPClient initializes correctly."""
    from app.infrastructure.email.smtp_client import BillionMailSMTPClient

    client = BillionMailSMTPClient(
        host="mail.example.com",
        port=587,
        user="test@example.com",
        password="secret",
        use_tls=True
    )

    assert client.host == "mail.example.com"
    assert client.port == 587
    assert client.user == "test@example.com"
    assert client.use_tls is True


def test_billion_mail_send_text_email():
    """Test sending plain text email via Billion Mail SMTP."""
    from app.infrastructure.email.smtp_client import BillionMailSMTPClient
    from app.infrastructure.email.models import EmailMessage, EmailRecipient

    client = BillionMailSMTPClient(
        host="mail.example.com",
        port=587,
        user="sender@example.com",
        password="secret"
    )

    recipient = EmailRecipient(email="test@example.com", name="Test User")
    message = EmailMessage(
        to=recipient,
        subject="Test Email",
        body_text="This is a test"
    )

    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = client.send(message)

        assert result is True
        mock_server.send_message.assert_called_once()


def test_billion_mail_send_html_email():
    """Test sending HTML email with plain text fallback."""
    from app.infrastructure.email.smtp_client import BillionMailSMTPClient
    from app.infrastructure.email.models import EmailMessage, EmailRecipient

    client = BillionMailSMTPClient(
        host="mail.example.com",
        port=587,
        user="sender@example.com",
        password="secret"
    )

    recipient = EmailRecipient(email="test@example.com", name="Test User")
    message = EmailMessage(
        to=recipient,
        subject="Test Email",
        body_text="Plain text",
        body_html="<p>HTML version</p>"
    )

    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = client.send(message)

        assert result is True
        mock_server.send_message.assert_called_once()


def test_billion_mail_send_with_attachments():
    """Test sending email with attachments."""
    from app.infrastructure.email.smtp_client import BillionMailSMTPClient
    from app.infrastructure.email.models import EmailMessage, EmailRecipient, EmailAttachment

    client = BillionMailSMTPClient(
        host="mail.example.com",
        port=587,
        user="sender@example.com",
        password="secret"
    )

    recipient = EmailRecipient(email="test@example.com", name="Test User")
    attachment = EmailAttachment(
        filename="report.pdf",
        content=b"PDF content",
        content_type="application/pdf"
    )

    message = EmailMessage(
        to=recipient,
        subject="Report",
        body_text="See attached",
        attachments=[attachment]
    )

    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = client.send(message)

        assert result is True
        mock_server.send_message.assert_called_once()


def test_billion_mail_send_with_tls():
    """Test SMTP client uses STARTTLS when enabled."""
    from app.infrastructure.email.smtp_client import BillionMailSMTPClient
    from app.infrastructure.email.models import EmailMessage, EmailRecipient

    client = BillionMailSMTPClient(
        host="mail.example.com",
        port=587,
        user="sender@example.com",
        password="secret",
        use_tls=True
    )

    recipient = EmailRecipient(email="test@example.com", name="Test User")
    message = EmailMessage(
        to=recipient,
        subject="Test",
        body_text="Test"
    )

    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        client.send(message)

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("sender@example.com", "secret")


def test_billion_mail_send_handles_smtp_failure():
    """Test SMTP client handles connection failures gracefully."""
    from app.infrastructure.email.smtp_client import BillionMailSMTPClient
    from app.infrastructure.email.models import EmailMessage, EmailRecipient

    client = BillionMailSMTPClient(
        host="mail.example.com",
        port=587,
        user="sender@example.com",
        password="secret"
    )

    recipient = EmailRecipient(email="test@example.com", name="Test User")
    message = EmailMessage(
        to=recipient,
        subject="Test",
        body_text="Test"
    )

    with patch('smtplib.SMTP') as mock_smtp:
        mock_smtp.side_effect = SMTPException("Connection failed")

        result = client.send(message)

        assert result is False


def test_email_service_initialization():
    """Test NotificationEmailService initializes correctly."""
    from app.infrastructure.email.email_service import NotificationEmailService
    from app.core.config import settings

    with patch('app.infrastructure.email.email_service.PGMQClient'):
        service = NotificationEmailService(settings)

        assert service is not None


def test_email_service_send_material_created_notification():
    """Test sending material created notification."""
    from app.infrastructure.email.email_service import NotificationEmailService
    from app.core.config import settings

    with patch('app.infrastructure.email.email_service.PGMQClient'):
        service = NotificationEmailService(settings)

        with patch.object(service.smtp_client, 'send', return_value=True):
            result = service.send_material_created(
                recipient_email="test@example.com",
                recipient_name="Test User",
                material_code="MAT-001",
                material_description="Test Material",
                created_by="John Doe",
                base_uom="EA"
            )

            assert result is True


def test_email_service_send_work_order_released_notification():
    """Test sending work order released notification."""
    from app.infrastructure.email.email_service import NotificationEmailService
    from app.core.config import settings

    with patch('app.infrastructure.email.email_service.PGMQClient'):
        service = NotificationEmailService(settings)

        with patch.object(service.smtp_client, 'send', return_value=True):
            result = service.send_work_order_released(
                recipient_email="test@example.com",
                recipient_name="Test User",
                work_order_number="WO-12345",
                material_code="MAT-001",
                quantity=100,
                status="Released"
            )

            assert result is True


def test_email_service_send_low_stock_alert():
    """Test sending low stock alert notification."""
    from app.infrastructure.email.email_service import NotificationEmailService
    from app.core.config import settings

    with patch('app.infrastructure.email.email_service.PGMQClient'):
        service = NotificationEmailService(settings)

        with patch.object(service.smtp_client, 'send', return_value=True):
            result = service.send_low_stock_alert(
                recipient_email="test@example.com",
                recipient_name="Test User",
                material_code="MAT-001",
                material_description="Test Material",
                current_stock=5,
                reorder_point=10,
                warehouse="WH-01"
            )

            assert result is True


def test_email_service_enqueues_to_pgmq():
    """Test email service can enqueue emails to PGMQ for async processing."""
    from app.infrastructure.email.email_service import NotificationEmailService
    from app.core.config import settings

    with patch('app.infrastructure.email.email_service.PGMQClient'):
        service = NotificationEmailService(settings)

        with patch.object(service, '_enqueue_email') as mock_enqueue:
            service.send_material_created_async(
                recipient_email="test@example.com",
                recipient_name="Test User",
                material_code="MAT-001",
                material_description="Test Material",
                created_by="John Doe",
                base_uom="EA"
            )

            mock_enqueue.assert_called_once()


def test_email_service_with_custom_from_address():
    """Test email service supports custom from address."""
    from app.infrastructure.email.email_service import NotificationEmailService
    from app.core.config import settings

    with patch('app.infrastructure.email.email_service.PGMQClient'):
        service = NotificationEmailService(settings, from_email="custom@example.com")

        assert service.from_email == "custom@example.com"
