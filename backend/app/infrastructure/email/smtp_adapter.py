"""SMTP email adapter implementation."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from app.application.services.email_service import EmailService
from app.core.config import Settings

logger = logging.getLogger(__name__)


class SMTPEmailAdapter(EmailService):
    """SMTP email service adapter.

    Implements EmailService interface using standard SMTP protocol.
    Supports both plain text and HTML emails with optional TLS encryption.
    """

    def __init__(self, settings: Settings):
        """Initialize SMTP adapter with configuration settings.

        Args:
            settings: Application settings containing SMTP configuration
        """
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_TLS

    def send_email(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send email via SMTP.

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
            # Create message container
            if html_body:
                msg = MIMEMultipart('alternative')
                msg.attach(MIMEText(body, 'plain'))
                msg.attach(MIMEText(html_body, 'html'))
            else:
                msg = MIMEText(body, 'plain')

            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email

            # Send email via SMTP
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {str(e)}")
            return False
