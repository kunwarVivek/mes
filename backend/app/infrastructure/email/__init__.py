"""Email infrastructure layer containing email service adapters."""
from app.infrastructure.email.smtp_adapter import SMTPEmailAdapter
from app.infrastructure.email.sendgrid_adapter import SendGridEmailAdapter
from app.infrastructure.email.aws_ses_adapter import AWSEmailAdapter
from app.infrastructure.email.email_factory import EmailServiceFactory
from app.infrastructure.email.smtp_client import BillionMailSMTPClient
from app.infrastructure.email.email_service import NotificationEmailService
from app.infrastructure.email.templates import TemplateManager
from app.infrastructure.email.models import (
    EmailRecipient,
    EmailMessage,
    EmailAttachment,
    EmailStatus,
    EmailAuditLog
)

__all__ = [
    'SMTPEmailAdapter',
    'SendGridEmailAdapter',
    'AWSEmailAdapter',
    'EmailServiceFactory',
    'BillionMailSMTPClient',
    'NotificationEmailService',
    'TemplateManager',
    'EmailRecipient',
    'EmailMessage',
    'EmailAttachment',
    'EmailStatus',
    'EmailAuditLog',
]
