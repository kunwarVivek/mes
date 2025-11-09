"""Email service factory for creating email adapter instances."""
from typing import Literal

from app.application.services.email_service import EmailService
from app.infrastructure.email.smtp_adapter import SMTPEmailAdapter
from app.infrastructure.email.sendgrid_adapter import SendGridEmailAdapter
from app.infrastructure.email.aws_ses_adapter import AWSEmailAdapter
from app.core.config import Settings


class EmailServiceFactory:
    """Factory for creating email service adapter instances.

    Creates the appropriate email service adapter based on configuration,
    enabling runtime selection of email providers without code changes.
    """

    @staticmethod
    def create(settings: Settings) -> EmailService:
        """Create email service adapter based on configuration.

        Args:
            settings: Application settings containing email provider configuration

        Returns:
            EmailService: Configured email service adapter instance

        Raises:
            ValueError: If EMAIL_PROVIDER is not a valid provider type
        """
        provider = settings.EMAIL_PROVIDER

        if provider == "smtp":
            return SMTPEmailAdapter(settings)
        elif provider == "sendgrid":
            return SendGridEmailAdapter(settings)
        elif provider == "aws_ses":
            return AWSEmailAdapter(settings)
        else:
            # This should never happen due to Literal type constraint
            raise ValueError(f"Invalid email provider: {provider}")
