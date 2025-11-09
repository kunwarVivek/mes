"""Unit tests for email models and DTOs."""
import pytest
from datetime import datetime
from pydantic import ValidationError


def test_email_recipient_creation():
    """Test EmailRecipient DTO creation."""
    from app.infrastructure.email.models import EmailRecipient

    recipient = EmailRecipient(
        email="test@example.com",
        name="Test User"
    )

    assert recipient.email == "test@example.com"
    assert recipient.name == "Test User"


def test_email_recipient_email_validation():
    """Test EmailRecipient validates email format."""
    from app.infrastructure.email.models import EmailRecipient

    with pytest.raises(ValidationError):
        EmailRecipient(email="invalid-email", name="Test")


def test_email_message_creation():
    """Test EmailMessage DTO creation with all fields."""
    from app.infrastructure.email.models import EmailMessage, EmailRecipient

    recipient = EmailRecipient(email="test@example.com", name="Test User")

    message = EmailMessage(
        to=recipient,
        subject="Test Subject",
        body_text="Plain text body",
        body_html="<p>HTML body</p>",
        from_email="sender@example.com",
        from_name="Sender Name"
    )

    assert message.to.email == "test@example.com"
    assert message.subject == "Test Subject"
    assert message.body_text == "Plain text body"
    assert message.body_html == "<p>HTML body</p>"
    assert message.from_email == "sender@example.com"
    assert message.from_name == "Sender Name"


def test_email_message_minimal_creation():
    """Test EmailMessage creation with minimal required fields."""
    from app.infrastructure.email.models import EmailMessage, EmailRecipient

    recipient = EmailRecipient(email="test@example.com", name="Test User")

    message = EmailMessage(
        to=recipient,
        subject="Test",
        body_text="Text"
    )

    assert message.to.email == "test@example.com"
    assert message.body_html is None
    assert message.attachments == []


def test_email_message_with_attachments():
    """Test EmailMessage with attachments."""
    from app.infrastructure.email.models import EmailMessage, EmailRecipient, EmailAttachment

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

    assert len(message.attachments) == 1
    assert message.attachments[0].filename == "report.pdf"
    assert message.attachments[0].content_type == "application/pdf"


def test_email_audit_log_entry():
    """Test EmailAuditLog model for tracking sent emails."""
    from app.infrastructure.email.models import EmailAuditLog, EmailStatus

    log = EmailAuditLog(
        recipient_email="test@example.com",
        subject="Test Email",
        status=EmailStatus.PENDING,
        queue_msg_id=123
    )

    assert log.recipient_email == "test@example.com"
    assert log.status == EmailStatus.PENDING
    assert log.queue_msg_id == 123
    assert log.sent_at is None
    assert log.error_message is None


def test_email_audit_log_status_transitions():
    """Test EmailAuditLog status transitions."""
    from app.infrastructure.email.models import EmailAuditLog, EmailStatus

    log = EmailAuditLog(
        recipient_email="test@example.com",
        subject="Test",
        status=EmailStatus.PENDING
    )

    # Mark as sent
    log.status = EmailStatus.SENT
    log.sent_at = datetime.utcnow()
    assert log.status == EmailStatus.SENT
    assert log.sent_at is not None

    # Mark as failed
    log.status = EmailStatus.FAILED
    log.error_message = "SMTP connection failed"
    assert log.status == EmailStatus.FAILED
    assert log.error_message == "SMTP connection failed"
