"""AWS SES email adapter implementation."""
from typing import Optional, Any
import logging

import boto3
from botocore.exceptions import ClientError

from app.application.services.email_service import EmailService
from app.core.config import Settings

logger = logging.getLogger(__name__)


class AWSEmailAdapter(EmailService):
    """AWS SES email service adapter.

    Implements EmailService interface using Amazon Simple Email Service (SES).
    Supports both plain text and HTML emails via AWS SDK (boto3).
    """

    def __init__(self, settings: Settings, client: Optional[Any] = None):
        """Initialize AWS SES adapter with credentials.

        Args:
            settings: Application settings containing AWS SES configuration
            client: Optional SES client instance (for testing)
        """
        self.region = settings.AWS_SES_REGION
        if client:
            self.client = client
        else:
            self.client = boto3.client(
                'ses',
                region_name=self.region,
                aws_access_key_id=settings.AWS_SES_ACCESS_KEY,
                aws_secret_access_key=settings.AWS_SES_SECRET_KEY
            )

    def send_email(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send email via AWS SES.

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
            # Prepare email body
            body_content = {'Text': {'Charset': 'UTF-8', 'Data': body}}
            if html_body:
                body_content['Html'] = {'Charset': 'UTF-8', 'Data': html_body}

            # Send email via AWS SES
            response = self.client.send_email(
                Source=from_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Charset': 'UTF-8', 'Data': subject},
                    'Body': body_content
                }
            )

            logger.info(f"Email sent successfully via AWS SES to {to_email}. MessageId: {response['MessageId']}")
            return True

        except ClientError as e:
            logger.error(f"AWS SES ClientError: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email via AWS SES: {str(e)}")
            return False
