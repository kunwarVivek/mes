"""Abstract email service interface for pluggable email providers."""
from abc import ABC, abstractmethod
from typing import Optional


class EmailService(ABC):
    """Abstract base class for email service implementations.

    Defines the contract that all email service adapters must implement,
    enabling pluggable email providers (SMTP, SendGrid, AWS SES, etc.).
    """

    @abstractmethod
    def send_email(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send an email message.

        Args:
            from_email: Sender's email address
            to_email: Recipient's email address
            subject: Email subject line
            body: Plain text email body
            html_body: Optional HTML email body

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        pass
