"""SendGrid email adapter implementation."""
from typing import Optional
import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content

from app.application.services.email_service import EmailService
from app.core.config import Settings

logger = logging.getLogger(__name__)


class SendGridEmailAdapter(EmailService):
    """SendGrid email service adapter.

    Implements EmailService interface using SendGrid API.
    Supports both plain text and HTML emails via SendGrid's REST API.
    """

    def __init__(self, settings: Settings, client: Optional[SendGridAPIClient] = None):
        """Initialize SendGrid adapter with API key.

        Args:
            settings: Application settings containing SendGrid configuration
            client: Optional SendGrid client instance (for testing)
        """
        self.api_key = settings.SENDGRID_API_KEY
        self.client = client or SendGridAPIClient(self.api_key)

    def send_email(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send email via SendGrid API.

        Args:
            from_email: Sender's email address
            to_email: Recipient's email address
            subject: Email subject line
            body: Plain text email body
            html_body: Optional HTML email body

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message with plain text content
            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=body
            )

            # Add HTML content if provided
            if html_body:
                message.add_content(Content("text/html", html_body))

            # Send email via SendGrid API
            response = self.client.send(message)

            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully via SendGrid to {to_email}")
                return True
            else:
                logger.error(f"SendGrid returned status code: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {str(e)}")
            return False
