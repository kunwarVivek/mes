"""Billion Mail SMTP client for email delivery."""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional

from app.infrastructure.email.models import EmailMessage

logger = logging.getLogger(__name__)


class BillionMailSMTPClient:
    """SMTP client specifically configured for Billion Mail (self-hosted).

    Handles connection, authentication, and email delivery through
    Billion Mail SMTP server with support for TLS, attachments,
    and HTML emails.
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        use_tls: bool = True
    ):
        """Initialize Billion Mail SMTP client.

        Args:
            host: SMTP server hostname
            port: SMTP server port (typically 587 for TLS, 25 for plain)
            user: SMTP authentication username
            password: SMTP authentication password
            use_tls: Whether to use STARTTLS encryption
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.use_tls = use_tls

    def send(self, message: EmailMessage) -> bool:
        """Send email via Billion Mail SMTP.

        Args:
            message: EmailMessage DTO containing all email details

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Create MIME message
            mime_msg = self._create_mime_message(message)

            # Connect to SMTP server and send
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()

                if self.user and self.password:
                    server.login(self.user, self.password)

                server.send_message(mime_msg)

            logger.info(f"Email sent successfully to {message.to.email}")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email to {message.to.email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {message.to.email}: {e}")
            return False

    def _create_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        """Create MIME message from EmailMessage DTO.

        Args:
            message: EmailMessage DTO

        Returns:
            MIMEMultipart: Properly formatted MIME message
        """
        # Determine from address
        from_email = message.from_email or self.user
        from_name = message.from_name or from_email

        # Create message container
        if message.body_html or message.attachments:
            mime_msg = MIMEMultipart('mixed')

            # Create alternative part for text/html
            if message.body_html:
                msg_alternative = MIMEMultipart('alternative')
                msg_alternative.attach(MIMEText(message.body_text, 'plain', 'utf-8'))
                msg_alternative.attach(MIMEText(message.body_html, 'html', 'utf-8'))
                mime_msg.attach(msg_alternative)
            else:
                mime_msg.attach(MIMEText(message.body_text, 'plain', 'utf-8'))
        else:
            mime_msg = MIMEMultipart()
            mime_msg.attach(MIMEText(message.body_text, 'plain', 'utf-8'))

        # Set headers
        mime_msg['Subject'] = message.subject
        mime_msg['From'] = f"{from_name} <{from_email}>"
        mime_msg['To'] = f"{message.to.name} <{message.to.email}>"

        # Add attachments
        for attachment in message.attachments:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.content)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment.filename}'
            )
            mime_msg.attach(part)

        return mime_msg
