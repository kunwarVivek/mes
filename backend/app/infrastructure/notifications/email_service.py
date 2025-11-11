"""
Email Service - Send transactional emails

Supports multiple email providers:
- SMTP (Gmail, SendGrid, Mailgun)
- AWS SES
- Development mode (console logging)

Configuration via environment variables.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import os

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Email message data"""

    to: List[str]
    subject: str
    html_body: str
    text_body: Optional[str] = None
    from_address: Optional[str] = None
    reply_to: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


class EmailService:
    """
    Email service for sending transactional emails

    Supports:
    - SMTP (Gmail, SendGrid, Mailgun, custom)
    - Development mode (logs to console)
    - Template rendering
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_address: Optional[str] = None,
        from_name: Optional[str] = None,
        use_tls: bool = True,
        development_mode: bool = False,
    ):
        """
        Initialize email service

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port (587 for TLS, 465 for SSL)
            smtp_username: SMTP username
            smtp_password: SMTP password
            from_address: Default 'from' email address
            from_name: Default 'from' name
            use_tls: Use TLS encryption (default: True)
            development_mode: Log emails instead of sending (default: False)
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.getenv("SMTP_USERNAME")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_address = from_address or os.getenv(
            "SMTP_FROM_ADDRESS", "noreply@unison-mes.com"
        )
        self.from_name = from_name or os.getenv("SMTP_FROM_NAME", "Unison MES")
        self.use_tls = use_tls
        self.development_mode = development_mode or not self.smtp_host

        if self.development_mode:
            logger.warning(
                "Email service in DEVELOPMENT MODE - emails will be logged, not sent"
            )

    def send(self, message: EmailMessage) -> bool:
        """
        Send email message

        Args:
            message: EmailMessage instance

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if self.development_mode:
            return self._log_email(message)

        try:
            return self._send_smtp(message)
        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return False

    def _send_smtp(self, message: EmailMessage) -> bool:
        """Send email via SMTP"""
        try:
            # Create MIME message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = (
                f"{self.from_name} <{message.from_address or self.from_address}>"
            )
            msg["To"] = ", ".join(message.to)

            if message.reply_to:
                msg["Reply-To"] = message.reply_to

            if message.cc:
                msg["Cc"] = ", ".join(message.cc)

            # Attach text and HTML parts
            if message.text_body:
                part1 = MIMEText(message.text_body, "plain")
                msg.attach(part1)

            part2 = MIMEText(message.html_body, "html")
            msg.attach(part2)

            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)

                # Send to all recipients (to, cc, bcc)
                recipients = message.to + (message.cc or []) + (message.bcc or [])
                server.sendmail(self.from_address, recipients, msg.as_string())

            logger.info(f"Email sent successfully to {', '.join(message.to)}")
            return True

        except Exception as e:
            logger.error(f"SMTP error: {e}", exc_info=True)
            return False

    def _log_email(self, message: EmailMessage) -> bool:
        """Log email to console (development mode)"""
        logger.info("=" * 80)
        logger.info("📧 EMAIL (DEVELOPMENT MODE - NOT SENT)")
        logger.info("=" * 80)
        logger.info(f"From: {self.from_name} <{message.from_address or self.from_address}>")
        logger.info(f"To: {', '.join(message.to)}")
        if message.cc:
            logger.info(f"Cc: {', '.join(message.cc)}")
        logger.info(f"Subject: {message.subject}")
        logger.info("-" * 80)
        logger.info(message.html_body)
        logger.info("=" * 80)
        return True

    def send_trial_expiring_soon(
        self, to_email: str, user_name: str, days_remaining: int, trial_ends_at: datetime
    ) -> bool:
        """
        Send trial expiring soon notification

        Args:
            to_email: Recipient email
            user_name: User's name
            days_remaining: Days until trial expires
            trial_ends_at: Trial end date

        Returns:
            bool: True if sent successfully
        """
        subject = f"Your Unison MES trial expires in {days_remaining} days"

        html_body = self._render_trial_expiring_template(
            user_name=user_name,
            days_remaining=days_remaining,
            trial_ends_at=trial_ends_at,
        )

        message = EmailMessage(
            to=[to_email],
            subject=subject,
            html_body=html_body,
        )

        return self.send(message)

    def send_trial_expired(
        self, to_email: str, user_name: str, trial_ended_at: datetime
    ) -> bool:
        """
        Send trial expired notification

        Args:
            to_email: Recipient email
            user_name: User's name
            trial_ended_at: Trial end date

        Returns:
            bool: True if sent successfully
        """
        subject = "Your Unison MES trial has expired"

        html_body = self._render_trial_expired_template(
            user_name=user_name,
            trial_ended_at=trial_ended_at,
        )

        message = EmailMessage(
            to=[to_email],
            subject=subject,
            html_body=html_body,
        )

        return self.send(message)

    def send_payment_succeeded(
        self, to_email: str, user_name: str, amount_cents: int, invoice_url: str
    ) -> bool:
        """
        Send payment succeeded notification

        Args:
            to_email: Recipient email
            user_name: User's name
            amount_cents: Payment amount in cents
            invoice_url: URL to invoice

        Returns:
            bool: True if sent successfully
        """
        subject = "Payment received - Thank you!"

        html_body = self._render_payment_succeeded_template(
            user_name=user_name,
            amount_cents=amount_cents,
            invoice_url=invoice_url,
        )

        message = EmailMessage(
            to=[to_email],
            subject=subject,
            html_body=html_body,
        )

        return self.send(message)

    def send_payment_failed(
        self, to_email: str, user_name: str, amount_cents: int, retry_count: int
    ) -> bool:
        """
        Send payment failed notification

        Args:
            to_email: Recipient email
            user_name: User's name
            amount_cents: Payment amount in cents
            retry_count: Number of retry attempts

        Returns:
            bool: True if sent successfully
        """
        subject = "Action required: Payment failed"

        html_body = self._render_payment_failed_template(
            user_name=user_name,
            amount_cents=amount_cents,
            retry_count=retry_count,
        )

        message = EmailMessage(
            to=[to_email],
            subject=subject,
            html_body=html_body,
        )

        return self.send(message)

    def _render_trial_expiring_template(
        self, user_name: str, days_remaining: int, trial_ends_at: datetime
    ) -> str:
        """Render trial expiring email template"""
        urgency_color = "#dc2626" if days_remaining <= 2 else "#f59e0b" if days_remaining <= 6 else "#3b82f6"

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: {urgency_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
        <h1 style="margin: 0; font-size: 24px;">⏰ Trial Expiring Soon</h1>
    </div>

    <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px;">
        <p style="font-size: 16px;">Hi {user_name},</p>

        <p style="font-size: 16px;">Your <strong>Unison MES trial</strong> expires in <strong style="color: {urgency_color};">{days_remaining} days</strong>.</p>

        <p style="font-size: 14px; color: #666;">
            Trial ends: <strong>{trial_ends_at.strftime('%B %d, %Y')}</strong>
        </p>

        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px;">Don't lose access to:</p>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li>All your production data</li>
                <li>Work orders and schedules</li>
                <li>Quality records (NCRs)</li>
                <li>Team collaboration</li>
            </ul>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="https://app.unison-mes.com/pricing" style="background: {urgency_color}; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                Upgrade Now
            </a>
        </div>

        <p style="font-size: 14px; color: #666; text-align: center;">
            Plans start at just $49/month
        </p>
    </div>

    <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #999;">
        <p>Unison Manufacturing ERP</p>
        <p>
            <a href="https://unison-mes.com" style="color: #3b82f6; text-decoration: none;">Website</a> •
            <a href="https://app.unison-mes.com/billing" style="color: #3b82f6; text-decoration: none;">Manage Subscription</a>
        </p>
    </div>
</body>
</html>
"""

    def _render_trial_expired_template(
        self, user_name: str, trial_ended_at: datetime
    ) -> str:
        """Render trial expired email template"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #dc2626; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
        <h1 style="margin: 0; font-size: 24px;">Your Trial Has Ended</h1>
    </div>

    <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px;">
        <p style="font-size: 16px;">Hi {user_name},</p>

        <p style="font-size: 16px;">Your <strong>14-day trial</strong> ended on {trial_ended_at.strftime('%B %d, %Y')}.</p>

        <p style="font-size: 16px;">Your account has been suspended, but <strong>your data is safe</strong>. Subscribe now to regain access.</p>

        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #111;">What's Next?</h3>
            <p style="margin: 0; font-size: 14px;">
                1. Choose a plan that fits your needs<br>
                2. Enter payment details (secure via Stripe)<br>
                3. Instant reactivation - your data is waiting!
            </p>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="https://app.unison-mes.com/pricing" style="background: #dc2626; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                Subscribe Now
            </a>
        </div>

        <p style="font-size: 14px; color: #666; text-align: center;">
            Need help? <a href="mailto:support@unison-mes.com" style="color: #3b82f6;">Contact Support</a>
        </p>
    </div>

    <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #999;">
        <p>Unison Manufacturing ERP</p>
    </div>
</body>
</html>
"""

    def _render_payment_succeeded_template(
        self, user_name: str, amount_cents: int, invoice_url: str
    ) -> str:
        """Render payment succeeded email template"""
        amount_dollars = amount_cents / 100
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #10b981; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
        <h1 style="margin: 0; font-size: 24px;">✅ Payment Received</h1>
    </div>

    <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px;">
        <p style="font-size: 16px;">Hi {user_name},</p>

        <p style="font-size: 16px;">Thank you! Your payment of <strong>${amount_dollars:.2f}</strong> was processed successfully.</p>

        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <p style="margin: 0; font-size: 24px; color: #10b981; font-weight: 600;">${amount_dollars:.2f}</p>
            <p style="margin: 5px 0 0 0; font-size: 14px; color: #666;">Payment Confirmed</p>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{invoice_url}" style="background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 500; display: inline-block;">
                View Invoice
            </a>
        </div>

        <p style="font-size: 14px; color: #666;">
            Your subscription remains active. Thank you for choosing Unison MES!
        </p>
    </div>

    <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #999;">
        <p>Unison Manufacturing ERP</p>
    </div>
</body>
</html>
"""

    def _render_payment_failed_template(
        self, user_name: str, amount_cents: int, retry_count: int
    ) -> str:
        """Render payment failed email template"""
        amount_dollars = amount_cents / 100
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #dc2626; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
        <h1 style="margin: 0; font-size: 24px;">⚠️ Payment Failed</h1>
    </div>

    <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px;">
        <p style="font-size: 16px;">Hi {user_name},</p>

        <p style="font-size: 16px;">We were unable to process your payment of <strong>${amount_dollars:.2f}</strong>.</p>

        <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px; color: #991b1b;">
                <strong>Action Required:</strong> Please update your payment method to avoid service interruption.
            </p>
            {f'<p style="margin: 10px 0 0 0; font-size: 12px; color: #991b1b;">Retry attempt {retry_count} of 3</p>' if retry_count else ''}
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="https://app.unison-mes.com/billing" style="background: #dc2626; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                Update Payment Method
            </a>
        </div>

        <p style="font-size: 14px; color: #666;">
            Common causes: insufficient funds, expired card, incorrect billing address.
        </p>

        <p style="font-size: 14px; color: #666;">
            Need help? <a href="mailto:support@unison-mes.com" style="color: #3b82f6;">Contact Support</a>
        </p>
    </div>

    <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #999;">
        <p>Unison Manufacturing ERP</p>
    </div>
</body>
</html>
"""


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get email service singleton instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
